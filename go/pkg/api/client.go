package api

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"tickgrabber/pkg/models"
)

// Client API客户端
type Client struct {
	config *models.Config
	client *http.Client
}

// NewClient 创建新的API客户端
func NewClient(config *models.Config) *Client {
	return &Client{
		config: config,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// InterParkClient Interpark客户端
type InterParkClient struct {
	*Client
}

// NewInterParkClient 创建Interpark客户端
func NewInterParkClient(config *models.Config) *InterParkClient {
	return &InterParkClient{
		Client: NewClient(config),
	}
}

// Yes24Client Yes24客户端
type Yes24Client struct {
	*Client
}

// NewYes24Client 创建Yes24客户端
func NewYes24Client(config *models.Config) *Yes24Client {
	return &Yes24Client{
		Client: NewClient(config),
	}
}

// MelonClient Melon客户端
type MelonClient struct {
	*Client
}

// NewMelonClient 创建Melon客户端
func NewMelonClient(config *models.Config) *MelonClient {
	return &MelonClient{
		Client: NewClient(config),
	}
}

// LoginRequest 登录请求
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// LoginResponse 登录响应
type LoginResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Token   string `json:"token,omitempty"`
}

// TicketInfo 票务信息
type TicketInfo struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Price     int    `json:"price"`
	SeatType  string `json:"seat_type"`
	Available bool   `json:"available"`
	Quantity  int    `json:"quantity"`
	Venue     string `json:"venue"`
	Date      string `json:"date"`
	Time      string `json:"time"`
}

// PurchaseRequest 购买请求
type PurchaseRequest struct {
	TicketID string   `json:"ticket_id"`
	Quantity int      `json:"quantity"`
	Seats    []string `json:"seats,omitempty"`
}

// PurchaseResponse 购买响应
type PurchaseResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	OrderID string `json:"order_id,omitempty"`
}

// Login 登录
func (c *Client) Login(ctx context.Context, site string) error {
	log.Printf("登录到 %s", site)

	switch site {
	case "interpark":
		return c.loginInterpark(ctx)
	case "yes24":
		return c.loginYes24(ctx)
	case "melon":
		return c.loginMelon(ctx)
	default:
		return fmt.Errorf("不支持的网站: %s", site)
	}
}

// loginInterpark 登录Interpark
func (c *InterParkClient) Login(ctx context.Context) error {
	loginURL := c.config.Ticketing.Sites["interpark"].LoginURL

	req := LoginRequest{
		Username: c.config.User.Username,
		Password: c.config.User.Password,
	}

	resp, err := c.post(ctx, loginURL, req)
	if err != nil {
		return err
	}

	var loginResp LoginResponse
	err = json.Unmarshal(resp, &loginResp)
	if err != nil {
		return err
	}

	if !loginResp.Success {
		return fmt.Errorf("登录失败: %s", loginResp.Message)
	}

	log.Println("Interpark登录成功")
	return nil
}

// loginYes24 登录Yes24
func (c *Yes24Client) Login(ctx context.Context) error {
	loginURL := c.config.Ticketing.Sites["yes24"].LoginURL

	req := LoginRequest{
		Username: c.config.User.Username,
		Password: c.config.User.Password,
	}

	resp, err := c.post(ctx, loginURL, req)
	if err != nil {
		return err
	}

	var loginResp LoginResponse
	err = json.Unmarshal(resp, &loginResp)
	if err != nil {
		return err
	}

	if !loginResp.Success {
		return fmt.Errorf("登录失败: %s", loginResp.Message)
	}

	log.Println("Yes24登录成功")
	return nil
}

// loginMelon 登录Melon
func (c *MelonClient) Login(ctx context.Context) error {
	loginURL := c.config.Ticketing.Sites["melon"].LoginURL

	req := LoginRequest{
		Username: c.config.User.Username,
		Password: c.config.User.Password,
	}

	resp, err := c.post(ctx, loginURL, req)
	if err != nil {
		return err
	}

	var loginResp LoginResponse
	err = json.Unmarshal(resp, &loginResp)
	if err != nil {
		return err
	}

	if !loginResp.Success {
		return fmt.Errorf("登录失败: %s", loginResp.Message)
	}

	log.Println("Melon登录成功")
	return nil
}

// GetTicketInfo 获取票务信息
func (c *Client) GetTicketInfo(ctx context.Context, concertID string) ([]TicketInfo, error) {
	log.Printf("获取演唱会 %s 的票务信息", concertID)

	// 这里应该调用实际的API
	// 为了演示，返回模拟数据
	tickets := []TicketInfo{
		{
			ID:        "ticket_001",
			Name:      "VIP座位",
			Price:     150000,
			SeatType:  "VIP",
			Available: true,
			Quantity:  10,
			Venue:     "首尔奥林匹克体育场",
			Date:      "2024-12-25",
			Time:      "19:00",
		},
		{
			ID:        "ticket_002",
			Name:      "A区座位",
			Price:     120000,
			SeatType:  "A区",
			Available: true,
			Quantity:  50,
			Venue:     "首尔奥林匹克体育场",
			Date:      "2024-12-25",
			Time:      "19:00",
		},
	}

	return tickets, nil
}

// PurchaseTicket 购买票务
func (c *Client) PurchaseTicket(ctx context.Context, req PurchaseRequest) (*PurchaseResponse, error) {
	log.Printf("购买票务: %s, 数量: %d", req.TicketID, req.Quantity)

	// 这里应该调用实际的购买API
	// 为了演示，返回模拟响应
	resp := &PurchaseResponse{
		Success: true,
		Message: "购买成功",
		OrderID: "order_12345",
	}

	log.Printf("购票成功，订单号: %s", resp.OrderID)
	return resp, nil
}

// CheckAvailability 检查票务可用性
func (c *Client) CheckAvailability(ctx context.Context, concertID string) (bool, error) {
	log.Printf("检查演唱会 %s 的票务可用性", concertID)

	// 这里应该调用实际的API检查
	// 为了演示，返回随机结果
	// 在实际应用中，这里会调用票务网站的API
	return true, nil
}

// post 发送POST请求
func (c *Client) post(ctx context.Context, url string, data interface{}) ([]byte, error) {
	jsonData, err := json.Marshal(data)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", c.config.Browser.UserAgent)

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP错误: %d, %s", resp.StatusCode, string(body))
	}

	return body, nil
}

// get 发送GET请求
func (c *Client) get(ctx context.Context, url string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("User-Agent", c.config.Browser.UserAgent)

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP错误: %d, %s", resp.StatusCode, string(body))
	}

	return body, nil
}

// 为了兼容性，添加这些方法到基础Client
func (c *Client) loginInterpark(ctx context.Context) error {
	client := NewInterParkClient(c.config)
	return client.Login(ctx)
}

func (c *Client) loginYes24(ctx context.Context) error {
	client := NewYes24Client(c.config)
	return client.Login(ctx)
}

func (c *Client) loginMelon(ctx context.Context) error {
	client := NewMelonClient(c.config)
	return client.Login(ctx)
}
