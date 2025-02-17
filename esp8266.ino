#include <ESP8266WiFi.h>          // ESP8266 WiFi功能库
#include <ESP8266WebServer.h>      // Web服务器库
#include <Servo.h>                 // 舵机控制库

// WiFi网络配置
const char* ssid = "canyouhearme";      // WiFi名称
const char* password = "icanhearyou";    // WiFi密码

// 舵机相关配置
Servo myservo;                // 创建舵机对象
int servoPin = 12;           // 舵机信号线连接到GPIO12引脚
int pos = 135;               // 舵机初始位置（中间位置135度）

// 定义舵机角度常量
const int UP_ANGLE = 90;     // 抬头角度（90度）
const int DOWN_ANGLE = 180;  // 低头角度（180度）
const int MID_ANGLE = 135;   // 中间位置（135度）

// 创建Web服务器实例，监听80端口（HTTP默认端口）
ESP8266WebServer server(80);

// 函数声明
void handleUp();    // 声明抬头函数
void handleDown();  // 声明低头函数

void setup() {
  // 初始化串口通信，波特率115200
  Serial.begin(115200);
  
  // 初始化舵机
  if(myservo.attach(servoPin)) {  // 将舵机连接到指定引脚
    Serial.println("舵机初始化成功");
  } else {
    Serial.println("舵机初始化失败");
  }
  myservo.write(MID_ANGLE);  // 设置舵机初始位置为135度
  
  // 连接WiFi网络
  WiFi.begin(ssid, password);
  Serial.print("正在连接WiFi");
  
  // 等待WiFi连接成功，设置超时时间
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED && timeout < 20) {
    delay(500);
    Serial.print(".");
    timeout++;
  }
  
  if (timeout >= 20) {
    Serial.println("\nWiFi连接失败！");
    return;  // 如果连接失败，停止后续操作
  }
  
  // 打印连接成功信息和IP地址
  Serial.println("\n已连接到WiFi");
  Serial.println("IP地址: " + WiFi.localIP().toString());
  
  // 设置HTTP请求处理路由
  server.on("/up", handleUp);     // 处理/up路径的请求（抬头）
  server.on("/down", handleDown); // 处理/down路径的请求（低头）
  
  // 启动Web服务器
  server.begin();
  Serial.println("HTTP服务器已启动");
}

void loop() {
  // 处理客户端请求
  server.handleClient();
}

// 处理抬头请求的函数
void handleUp() {
  Serial.println("收到抬头请求");
  
  // 先转到抬头位置（90度）
  myservo.write(UP_ANGLE);
  delay(1000);  // 等待舵机转动到位（1秒）
  
  // 然后回到中间位置（135度）
  myservo.write(MID_ANGLE);
  pos = MID_ANGLE;  // 更新当前位置记录
  
  // 发送响应给客户端
  server.send(200, "text/plain", "已完成抬头动作并返回中间位置");
  Serial.println("完成抬头动作");
}

// 处理低头请求的函数
void handleDown() {
  Serial.println("收到低头请求");
  
  // 先转到低头位置（180度）
  myservo.write(DOWN_ANGLE);
  delay(1000);  // 等待舵机转动到位（1秒）
  
  // 然后回到中间位置（135度）
  myservo.write(MID_ANGLE);
  pos = MID_ANGLE;  // 更新当前位置记录
  
  // 发送响应给客户端
  server.send(200, "text/plain", "已完成低头动作并返回中间位置");
  Serial.println("完成低头动作");
} 
