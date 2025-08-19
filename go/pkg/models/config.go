package models

import "time"

// Config 配置结构
type Config struct {
	App          AppConfig          `json:"app"`
	Browser      BrowserConfig      `json:"browser"`
	Ticketing    TicketingConfig    `json:"ticketing"`
	User         UserConfig         `json:"user"`
	Tickets      TicketsConfig      `json:"tickets"`
	Proxy        ProxyConfig        `json:"proxy"`
	Notification NotificationConfig `json:"notification"`
	Captcha      CaptchaConfig      `json:"captcha"`
	Logging      LoggingConfig      `json:"logging"`
	Concerts     []Concert          `json:"concerts"`
}

// AppConfig 应用配置
type AppConfig struct {
	Name     string `json:"name"`
	Version  string `json:"version"`
	Language string `json:"language"`
}

// BrowserConfig 浏览器配置
type BrowserConfig struct {
	Headless     bool   `json:"headless"`
	UserAgent    string `json:"user_agent"`
	Timeout      int    `json:"timeout"`
	ImplicitWait int    `json:"implicit_wait"`
}

// TicketingConfig 票务配置
type TicketingConfig struct {
	Sites           map[string]SiteConfig `json:"sites"`
	DefaultSite     string                `json:"default_site"`
	AutoRefresh     bool                  `json:"auto_refresh"`
	RefreshInterval float64               `json:"refresh_interval"`
	MaxRetries      int                   `json:"max_retries"`
	RetryDelay      float64               `json:"retry_delay"`
}

// SiteConfig 网站配置
type SiteConfig struct {
	Name      string `json:"name"`
	URL       string `json:"url"`
	LoginURL  string `json:"login_url"`
	SearchURL string `json:"search_url"`
}

// UserConfig 用户配置
type UserConfig struct {
	Username  string `json:"username"`
	Password  string `json:"password"`
	AutoLogin bool   `json:"auto_login"`
}

// TicketsConfig 票务配置
type TicketsConfig struct {
	MaxPrice        int             `json:"max_price"`
	PreferredSeats  []string        `json:"preferred_seats"`
	SeatPreferences SeatPreferences `json:"seat_preferences"`
}

// SeatPreferences 座位偏好
type SeatPreferences struct {
	FrontRow      bool `json:"front_row"`
	CenterSection bool `json:"center_section"`
	VipSection    bool `json:"vip_section"`
}

// ProxyConfig 代理配置
type ProxyConfig struct {
	Enabled  bool   `json:"enabled"`
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
}

// NotificationConfig 通知配置
type NotificationConfig struct {
	Email    EmailConfig    `json:"email"`
	Telegram TelegramConfig `json:"telegram"`
	Desktop  DesktopConfig  `json:"desktop"`
}

// EmailConfig 邮件配置
type EmailConfig struct {
	Enabled    bool   `json:"enabled"`
	SMTPServer string `json:"smtp_server"`
	SMTPPort   int    `json:"smtp_port"`
	Sender     string `json:"sender"`
	Password   string `json:"password"`
	Recipient  string `json:"recipient"`
}

// TelegramConfig Telegram配置
type TelegramConfig struct {
	Enabled  bool   `json:"enabled"`
	BotToken string `json:"bot_token"`
	ChatID   string `json:"chat_id"`
}

// DesktopConfig 桌面通知配置
type DesktopConfig struct {
	Enabled bool `json:"enabled"`
	Sound   bool `json:"sound"`
}

// CaptchaConfig 验证码配置
type CaptchaConfig struct {
	AutoSolve bool   `json:"auto_solve"`
	Service   string `json:"service"`
	APIKey    string `json:"api_key"`
	Timeout   int    `json:"timeout"`
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Level       string `json:"level"`
	File        string `json:"file"`
	MaxSize     string `json:"max_size"`
	BackupCount int    `json:"backup_count"`
}

// Concert 演唱会信息
type Concert struct {
	ID             string    `json:"id"`
	Name           string    `json:"name"`
	Artist         string    `json:"artist"`
	Venue          string    `json:"venue"`
	Date           string    `json:"date"`
	Time           string    `json:"time"`
	Site           string    `json:"site"`
	URL            string    `json:"url"`
	MaxPrice       int       `json:"max_price"`
	PreferredSeats []string  `json:"preferred_seats"`
	Status         string    `json:"status"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}
