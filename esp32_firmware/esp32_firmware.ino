#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>
#include <mbedtls/aes.h>
#include <mbedtls/base64.h>
#include <ArduinoJson.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>

// ==========================================
// CONFIGURATION
// ==========================================
const char* WIFI_SSID = "Akshat";
const char* WIFI_PASSWORD = "1234567890";
const String FIREBASE_URL = "https://micro-project-ee399-default-rtdb.firebaseio.com";

unsigned char aes_key[16] = {
  '1', '2', '3', '4', '5', '6', '7', '8', 
  '9', '0', 'a', 'b', 'c', 'd', 'e', 'f'
};

// ==========================================
// PINS & PERIPHERALS
// ==========================================
#define SS_PIN  5
#define RST_PIN 4
MFRC522 rfid(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 20, 4);

#define LED_PIN 12
#define BUZZER_PIN 13

// ==========================================
// RTOS & STATE
// ==========================================
QueueHandle_t uidQueue;
QueueHandle_t displayQueue;

// Anomaly Detection State
unsigned long scan_history[3] = {0,0,0};
bool is_locked = false;
unsigned long lock_timer = 0;

// ==========================================
// HELPER FUNCTIONS
// ==========================================
void unpad_pkcs7(unsigned char* data, int* length) {
  int pad_len = data[*length - 1];
  if (pad_len > 0 && pad_len <= 16) {
    *length -= pad_len;
    data[*length] = '\0';
  }
}

String decrypt_portfolio(String b64_ciphertext) {
  size_t decoded_len = 0;
  unsigned char* decoded = (unsigned char*)malloc(b64_ciphertext.length());
  mbedtls_base64_decode(decoded, b64_ciphertext.length(), &decoded_len, (const unsigned char*)b64_ciphertext.c_str(), b64_ciphertext.length());

  mbedtls_aes_context aes;
  mbedtls_aes_init(&aes);
  mbedtls_aes_setkey_dec(&aes, aes_key, 128); 

  unsigned char* decrypted = (unsigned char*)malloc(decoded_len + 1);
  for (int i = 0; i < decoded_len; i += 16) {
    mbedtls_aes_crypt_ecb(&aes, MBEDTLS_AES_DECRYPT, &decoded[i], &decrypted[i]);
  }
  
  int plaintext_len = decoded_len;
  unpad_pkcs7(decrypted, &plaintext_len);
  
  String result = String((char*)decrypted);
  mbedtls_aes_free(&aes);
  free(decoded);
  free(decrypted);

  return result;
}

void trigger_alert() {
  digitalWrite(LED_PIN, HIGH);
  tone(BUZZER_PIN, 1000, 500); 
  delay(500);
  digitalWrite(LED_PIN, LOW);
  noTone(BUZZER_PIN);
}

void trigger_lockdown_siren() {
  for(int i = 0; i < 6; i++) {
    digitalWrite(LED_PIN, HIGH);
    tone(BUZZER_PIN, 1500, 150);
    delay(150);
    digitalWrite(LED_PIN, LOW);
    tone(BUZZER_PIN, 1000, 150);
    delay(150);
  }
  noTone(BUZZER_PIN);
}

// ==========================================
// CORE 0: DATABASE & NETWORK LAYER (FREE RTOS)
// ==========================================
void NetworkTask(void *pvParameters) {
  while (true) {
    char uidMsg[20];
    
    // Wait infinitely until Core 1 passes a UID into the Queue
    if (xQueueReceive(uidQueue, &uidMsg, portMAX_DELAY) == pdPASS) {
      if (WiFi.status() == WL_CONNECTED) {
        String uid_str = String(uidMsg);
        HTTPClient http;
        String fetchUrl = FIREBASE_URL + "/users/" + uid_str + ".json";
        
        http.begin(fetchUrl);
        int httpCode = http.GET();
        
        String responseToSend = "ERROR";
        
        if (httpCode == 200) {
          String payload = http.getString();
          DynamicJsonDocument doc(1024);
          deserializeJson(doc, payload);
          
          if (doc.containsKey("portfolio_AES")) {
            String encrypted_data = doc["portfolio_AES"].as<String>();
            responseToSend = decrypt_portfolio(encrypted_data);
            Serial.println("Decrypted: " + responseToSend);
          } else {
            responseToSend = "NO_DATA";
          }
        }
        http.end();
        
        // Push the decrypted String back through Queue to Core 1 for LCD Rendering
        char outMsg[150];
        responseToSend.toCharArray(outMsg, 150);
        xQueueSend(displayQueue, &outMsg, portMAX_DELAY);
      }
    }
    
    // Background Market & Feed Polling (Every 10 secs)
    static unsigned long last_poll = 0;
    if (millis() - last_poll > 10000) {
      last_poll = millis();
      if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        // 1. Check for Crash Alert
        http.begin(FIREBASE_URL + "/public/market_alert.json");
        if (http.GET() == 200) {
           DynamicJsonDocument doc(256);
           deserializeJson(doc, http.getString());
           if (doc["market_crash"] == true) {
             char alertMsg[150] = "MARKET_CRASH_ALERT";
             xQueueSend(displayQueue, &alertMsg, 0);
           }
        }
        http.end();

        // 2. Fetch Idle Information Feed (Weather/Stock)
        http.begin(FIREBASE_URL + "/public/idle_feed.json");
        if (http.GET() == 200) {
           DynamicJsonDocument doc(256);
           deserializeJson(doc, http.getString());
           if (doc.containsKey("feed")) {
             String feedString = "FEED:" + doc["feed"].as<String>();
             char feedMsg[150];
             feedString.toCharArray(feedMsg, 150);
             xQueueSend(displayQueue, &feedMsg, 0);
           }
        }
        http.end();
      }
    }

    vTaskDelay(10 / portTICK_PERIOD_MS); // Yield to watchdog
  }
}

// ==========================================
// CORE 1: HARDWARE I/O LAYER (FREE RTOS)
// ==========================================
void HardwareTask(void *pvParameters) {
  while (true) {
    // 1. ANOMALY LOCKDOWN CHECK
    if (is_locked) {
      if (millis() - lock_timer > 15000) { // Lift lock after 15 seconds
        is_locked = false; 
        scan_history[0] = 0; scan_history[1] = 0; scan_history[2] = 0;
        lcd.clear();
      } else {
        lcd.setCursor(0,0);
        lcd.print("! SYSTEM LOCKED !");
        lcd.setCursor(0,1);
        lcd.print("ANTI-BRUTE FORCE ");
        vTaskDelay(1000 / portTICK_PERIOD_MS);
        continue;
      }
    }

    lcd.setCursor(0, 0);
    lcd.print("Scan RFID Card...");

    // 2. CHECK IF CORE 0 PUSHED SOMETHING TO QUEUE
    char incomingDisplay[150];
    if (xQueueReceive(displayQueue, &incomingDisplay, 0) == pdPASS) {
      String display_text = String(incomingDisplay);
      
      lcd.clear();
      if (display_text.startsWith("FEED:")) {
          // Display the idle kiosk feed
          lcd.setCursor(0, 0);
          lcd.print("- LIVE KIOSK --");
          String feed_text = display_text.substring(5); // remove FEED:
          
          if (feed_text.length() <= 16) {
             lcd.setCursor(0, 1);
             lcd.print(feed_text);
             vTaskDelay(3000 / portTICK_PERIOD_MS); // show feed for 3 secs
          } else {
             // paginated feed
             for (int i = 0; i < feed_text.length(); i += 16) {
                lcd.setCursor(0, 1);
                lcd.print("                ");
                lcd.setCursor(0, 1);
                int end_idx = i + 16;
                if (end_idx > feed_text.length()) end_idx = feed_text.length();
                lcd.print(feed_text.substring(i, end_idx));
                vTaskDelay(2500 / portTICK_PERIOD_MS);
             }
          }
      } 
      else if (display_text == "ERROR") {
        lcd.print("HTTP Error"); vTaskDelay(2000 / portTICK_PERIOD_MS);
      } else if (display_text == "NO_DATA") {
        lcd.print("No Portfolio Data"); vTaskDelay(2000 / portTICK_PERIOD_MS);
      } else if (display_text == "MARKET_CRASH_ALERT") {
        lcd.print("! MARKET CRASH !");
        lcd.setCursor(0, 1);
        lcd.print("CHK DASHBOARD!!!");
        trigger_lockdown_siren();
        vTaskDelay(3000 / portTICK_PERIOD_MS);
      } else {
        // Secure Portfolio Decryption Mode
        lcd.setCursor(0, 0);
        lcd.print("- AI Portfolio  -");
        
        // Smart Pagination Logic
        int text_len = display_text.length();
        for (int i = 0; i < text_len; i += 16) {
          lcd.setCursor(0, 1);
          lcd.print("                ");
          lcd.setCursor(0, 1);
          int end_idx = i + 16;
          if (end_idx > text_len) end_idx = text_len;
          lcd.print(display_text.substring(i, end_idx));
          vTaskDelay(2500 / portTICK_PERIOD_MS);
        }
        trigger_alert();
      }
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Scan RFID Card...");
    }

    // 3. RFID SCANNER CHECK (WITH ANOMALY STATE MACHINE)
    if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
      
      // Advance State Machine Memory
      scan_history[2] = scan_history[1];
      scan_history[1] = scan_history[0];
      scan_history[0] = millis();
      
      // Anomaly Filter: Did user scan 3 times extremely rapidly (under 5 seconds)?
      if (scan_history[2] > 0 && (scan_history[0] - scan_history[2] < 5000)) {
        is_locked = true;
        lock_timer = millis();
        lcd.clear();
        lcd.setCursor(0,0);
        lcd.print("BRUTE FORCE DET.");
        trigger_lockdown_siren();
        rfid.PICC_HaltA(); rfid.PCD_StopCrypto1();
        continue;
      }

      // Convert UID
      String uid_hex = "";
      for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) uid_hex += "0";
        uid_hex += String(rfid.uid.uidByte[i], HEX);
      }
      uid_hex.toUpperCase();

      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Authenticating..");
      lcd.setCursor(0, 1);
      lcd.print(uid_hex);

      // ASYNC PUSH UID TO CORE 0
      char uidMsg[20];
      uid_hex.toCharArray(uidMsg, 20);
      xQueueSend(uidQueue, &uidMsg, portMAX_DELAY);
      
      rfid.PICC_HaltA(); rfid.PCD_StopCrypto1();
    }
    
    // Always yield core clock back to OS
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }
}

// ==========================================
// SETUP & OS BOOTLOADER
// ==========================================
void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();
  lcd.init();
  lcd.backlight();
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Initialize Dual-Core Inter-Process Queues
  uidQueue = xQueueCreate(10, sizeof(char) * 20);
  displayQueue = xQueueCreate(5, sizeof(char) * 150);

  lcd.print("Connecting WiFi..");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  lcd.clear();

  // RTOS Task Deployment onto the Microchip
  xTaskCreatePinnedToCore(NetworkTask,  "Core0_DB", 8192, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(HardwareTask, "Core1_HW", 8192, NULL, 1, NULL, 1);
}

// Emptied standard loop - FreeRTOS entirely manages execution now
void loop() {
  vTaskDelete(NULL); 
}
