#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>
#include <mbedtls/aes.h>
#include <mbedtls/base64.h>
#include <ArduinoJson.h>

// ==========================================
// CONFIGURATION
// ==========================================
const char* WIFI_SSID = "Akshat";
const char* WIFI_PASSWORD = "1234567890";
const String FIREBASE_URL = "https://micro-project-ee399-default-rtdb.firebaseio.com";

// 16-byte AES-128 Key (Must match the Python Dashboard Key)
unsigned char aes_key[16] = {
  '1', '2', '3', '4', '5', '6', '7', '8', 
  '9', '0', 'a', 'b', 'c', 'd', 'e', 'f'
};

// ==========================================
// PINS & PERIPHERALS
// ==========================================
// RFID MFRC522 Pins
#define SS_PIN  5
#define RST_PIN 4
MFRC522 rfid(SS_PIN, RST_PIN);

// LCD Display (I2C addr usually 0x27)
LiquidCrystal_I2C lcd(0x27, 20, 4);

// Alerts
#define LED_PIN 12
#define BUZZER_PIN 13

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
  // Decode Base64 using mbedtls
  size_t decoded_len = 0;
  unsigned char* decoded = (unsigned char*)malloc(b64_ciphertext.length());
  mbedtls_base64_decode(decoded, b64_ciphertext.length(), &decoded_len, (const unsigned char*)b64_ciphertext.c_str(), b64_ciphertext.length());

  // Setup AES ECB Context
  mbedtls_aes_context aes;
  mbedtls_aes_init(&aes);
  mbedtls_aes_setkey_dec(&aes, aes_key, 128); // 128 bits

  // Decrypt block by block (16 bytes)
  unsigned char* decrypted = (unsigned char*)malloc(decoded_len + 1);
  for (int i = 0; i < decoded_len; i += 16) {
    mbedtls_aes_crypt_ecb(&aes, MBEDTLS_AES_DECRYPT, &decoded[i], &decrypted[i]);
  }
  
  // Unpad and null terminate
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

// ==========================================
// SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  
  // Initialize Peripherals
  SPI.begin();
  rfid.PCD_Init();
  lcd.init();
  lcd.backlight();
  
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Connect to WiFi
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi Connected!");
  delay(1000);
  lcd.clear();
}

// ==========================================
// MAIN LOOP
// ==========================================
void loop() {
  lcd.setCursor(0, 0);
  lcd.print("Scan RFID Card...");

  // Check for new card
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    delay(50);
    return;
  }

  // Extract UID
  String uid_hex = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid_hex += "0";
    uid_hex += String(rfid.uid.uidByte[i], HEX);
  }
  uid_hex.toUpperCase();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Authenticating:");
  lcd.setCursor(0, 1);
  lcd.print(uid_hex);
  Serial.println("Scanned UID: " + uid_hex);

  // Fetch Firebase Data
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String fetchUrl = FIREBASE_URL + "/users/" + uid_hex + ".json";
    
    http.begin(fetchUrl);
    int httpCode = http.GET();
    
    if (httpCode == 200) {
      String payload = http.getString();
      
      // Parse JSON
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, payload);
      
      if (doc.containsKey("portfolio_AES")) {
        String encrypted_data = doc["portfolio_AES"].as<String>();
        String decrypted_data = decrypt_portfolio(encrypted_data);
        
        Serial.println("Decrypted: " + decrypted_data);
        
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("--- Portfolio ---");
        
        // Paginate portfolio text safely on Row 1 (16 characters at a time)
        int text_len = decrypted_data.length();
        for (int i = 0; i < text_len; i += 16) {
          lcd.setCursor(0, 1);
          lcd.print("                "); // clear the row
          lcd.setCursor(0, 1);
          
          int end_idx = i + 16;
          if (end_idx > text_len) end_idx = text_len;
          
          lcd.print(decrypted_data.substring(i, end_idx));
          delay(2500); // Wait 2.5 seconds per chunk before scrolling to the next
        }

        trigger_alert(); // Beep when finished
        delay(1000);
      } else {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("No Portfolio Data");
        delay(3000);
      }
    } else {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("HTTP Err: " + String(httpCode));
      delay(3000);
    }
    http.end(); // Free resources
  }
  
  // Reset for next scan
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  lcd.clear();
}
