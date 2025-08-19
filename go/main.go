package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"tickgrabber/pkg/api"
	"tickgrabber/pkg/browser"
	"tickgrabber/pkg/models"
)

var (
	configFile = flag.String("config", "config/config.json", "配置文件路径")
	concertID  = flag.String("concert", "", "演唱会ID")
	headless   = flag.Bool("headless", false, "无头模式")
	debug      = flag.Bool("debug", false, "调试模式")
)

func main() {
	flag.Parse()

	// 设置日志
	if *debug {
		log.SetFlags(log.LstdFlags | log.Lshortfile)
	}

	log.Println("韩国演唱会抢票系统 - Go版本启动")

	// 加载配置
	config, err := loadConfig(*configFile)
	if err != nil {
		log.Fatalf("加载配置失败: %v", err)
	}

	// 创建浏览器实例
	browser, err := browser.NewBrowser(&browser.Options{
		Headless: *headless,
		Debug:    *debug,
		Timeout:  30 * time.Second,
	})
	if err != nil {
		log.Fatalf("创建浏览器失败: %v", err)
	}
	defer browser.Close()

	// 创建API客户端
	apiClient := api.NewClient(config)

	// 获取演唱会信息
	var targetConcert *models.Concert
	if *concertID != "" {
		targetConcert = findConcertByID(config.Concerts, *concertID)
		if targetConcert == nil {
			log.Fatalf("找不到ID为 %s 的演唱会", *concertID)
		}
	} else {
		// 如果没有指定演唱会，使用第一个
		if len(config.Concerts) == 0 {
			log.Fatal("配置中没有演唱会信息")
		}
		targetConcert = &config.Concerts[0]
	}

	log.Printf("开始抢票: %s", targetConcert.Name)

	// 创建抢票任务
	task := NewTicketGrabber(browser, apiClient, config)

	// 设置信号处理
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Println("收到退出信号，正在停止...")
		cancel()
	}()

	// 开始抢票
	err = task.Start(ctx, targetConcert)
	if err != nil {
		log.Fatalf("抢票失败: %v", err)
	}
}

// TicketGrabber 抢票器
type TicketGrabber struct {
	browser   *browser.Browser
	apiClient *api.Client
	config    *models.Config
}

// NewTicketGrabber 创建新的抢票器
func NewTicketGrabber(browser *browser.Browser, apiClient *api.Client, config *models.Config) *TicketGrabber {
	return &TicketGrabber{
		browser:   browser,
		apiClient: apiClient,
		config:    config,
	}
}

// Start 开始抢票
func (tg *TicketGrabber) Start(ctx context.Context, concert *models.Concert) error {
	log.Printf("开始为演唱会 %s 抢票", concert.Name)

	// 登录票务网站
	err := tg.login(ctx)
	if err != nil {
		return fmt.Errorf("登录失败: %v", err)
	}

	// 进入演唱会页面
	err = tg.navigateToConcert(ctx, concert)
	if err != nil {
		return fmt.Errorf("进入演唱会页面失败: %v", err)
	}

	// 开始监控票务
	return tg.monitorTickets(ctx, concert)
}

// login 登录票务网站
func (tg *TicketGrabber) login(ctx context.Context) error {
	log.Println("正在登录票务网站...")

	// 根据配置选择登录方式
	switch tg.config.Ticketing.DefaultSite {
	case "interpark":
		return tg.loginInterpark(ctx)
	case "yes24":
		return tg.loginYes24(ctx)
	case "melon":
		return tg.loginMelon(ctx)
	default:
		return fmt.Errorf("不支持的票务网站: %s", tg.config.Ticketing.DefaultSite)
	}
}

// loginInterpark 登录Interpark
func (tg *TicketGrabber) loginInterpark(ctx context.Context) error {
	loginURL := tg.config.Ticketing.Sites["interpark"].LoginURL

	err := tg.browser.Navigate(ctx, loginURL)
	if err != nil {
		return err
	}

	// 填写用户名和密码
	err = tg.browser.FillForm(ctx, map[string]string{
		"username": tg.config.User.Username,
		"password": tg.config.User.Password,
	})
	if err != nil {
		return err
	}

	// 提交登录表单
	err = tg.browser.SubmitForm(ctx)
	if err != nil {
		return err
	}

	log.Println("Interpark登录成功")
	return nil
}

// loginYes24 登录Yes24
func (tg *TicketGrabber) loginYes24(ctx context.Context) error {
	loginURL := tg.config.Ticketing.Sites["yes24"].LoginURL

	err := tg.browser.Navigate(ctx, loginURL)
	if err != nil {
		return err
	}

	// 填写登录信息
	err = tg.browser.FillForm(ctx, map[string]string{
		"userId": tg.config.User.Username,
		"userPw": tg.config.User.Password,
	})
	if err != nil {
		return err
	}

	// 提交登录
	err = tg.browser.SubmitForm(ctx)
	if err != nil {
		return err
	}

	log.Println("Yes24登录成功")
	return nil
}

// loginMelon 登录Melon
func (tg *TicketGrabber) loginMelon(ctx context.Context) error {
	loginURL := tg.config.Ticketing.Sites["melon"].LoginURL

	err := tg.browser.Navigate(ctx, loginURL)
	if err != nil {
		return err
	}

	// 填写登录信息
	err = tg.browser.FillForm(ctx, map[string]string{
		"id": tg.config.User.Username,
		"pw": tg.config.User.Password,
	})
	if err != nil {
		return err
	}

	// 提交登录
	err = tg.browser.SubmitForm(ctx)
	if err != nil {
		return err
	}

	log.Println("Melon登录成功")
	return nil
}

// navigateToConcert 进入演唱会页面
func (tg *TicketGrabber) navigateToConcert(ctx context.Context, concert *models.Concert) error {
	log.Printf("正在进入演唱会页面: %s", concert.URL)

	err := tg.browser.Navigate(ctx, concert.URL)
	if err != nil {
		return err
	}

	// 等待页面加载
	time.Sleep(2 * time.Second)

	log.Println("已进入演唱会页面")
	return nil
}

// monitorTickets 监控票务
func (tg *TicketGrabber) monitorTickets(ctx context.Context, concert *models.Concert) error {
	log.Println("开始监控票务...")

	refreshInterval := time.Duration(tg.config.Ticketing.RefreshInterval*1000) * time.Millisecond
	ticker := time.NewTicker(refreshInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("抢票任务已停止")
			return nil
		case <-ticker.C:
			// 检查是否有票
			available, err := tg.checkTicketAvailability(ctx)
			if err != nil {
				log.Printf("检查票务状态失败: %v", err)
				continue
			}

			if available {
				log.Println("发现可用票务！")

				// 尝试购买
				err = tg.purchaseTicket(ctx, concert)
				if err != nil {
					log.Printf("购买失败: %v", err)
					continue
				}

				log.Println("购票成功！")
				return nil
			}

			log.Println("暂无可用票务，继续监控...")
		}
	}
}

// checkTicketAvailability 检查票务可用性
func (tg *TicketGrabber) checkTicketAvailability(ctx context.Context) (bool, error) {
	// 检查页面上的票务状态
	selectors := []string{
		".ticket-available",
		".btn-buy",
		"[data-status='available']",
		".seat-available",
	}

	for _, selector := range selectors {
		exists, err := tg.browser.ElementExists(ctx, selector)
		if err != nil {
			continue
		}
		if exists {
			return true, nil
		}
	}

	return false, nil
}

// purchaseTicket 购买票务
func (tg *TicketGrabber) purchaseTicket(ctx context.Context, concert *models.Concert) error {
	log.Println("开始购买票务...")

	// 选择座位
	err := tg.selectSeats(ctx, concert)
	if err != nil {
		return fmt.Errorf("选择座位失败: %v", err)
	}

	// 确认购买
	err = tg.confirmPurchase(ctx)
	if err != nil {
		return fmt.Errorf("确认购买失败: %v", err)
	}

	// 处理支付
	err = tg.handlePayment(ctx)
	if err != nil {
		return fmt.Errorf("处理支付失败: %v", err)
	}

	log.Println("票务购买完成！")
	return nil
}

// selectSeats 选择座位
func (tg *TicketGrabber) selectSeats(ctx context.Context, concert *models.Concert) error {
	log.Println("正在选择座位...")

	// 根据偏好选择座位
	for _, preference := range concert.PreferredSeats {
		selector := fmt.Sprintf("[data-seat-type='%s']", preference)
		clicked, err := tg.browser.ClickElement(ctx, selector)
		if err == nil && clicked {
			log.Printf("已选择座位类型: %s", preference)
			return nil
		}
	}

	// 如果没有找到偏好座位，选择第一个可用座位
	clicked, err := tg.browser.ClickElement(ctx, ".seat-available")
	if err != nil || !clicked {
		return fmt.Errorf("无法选择座位")
	}

	log.Println("座位选择完成")
	return nil
}

// confirmPurchase 确认购买
func (tg *TicketGrabber) confirmPurchase(ctx context.Context) error {
	log.Println("确认购买...")

	// 点击购买按钮
	selectors := []string{
		".btn-purchase",
		".btn-buy",
		"[data-action='purchase']",
	}

	for _, selector := range selectors {
		clicked, err := tg.browser.ClickElement(ctx, selector)
		if err == nil && clicked {
			log.Println("购买按钮点击成功")
			return nil
		}
	}

	return fmt.Errorf("无法找到购买按钮")
}

// handlePayment 处理支付
func (tg *TicketGrabber) handlePayment(ctx context.Context) error {
	log.Println("处理支付...")

	// 等待支付页面加载
	time.Sleep(3 * time.Second)

	// 这里可以添加自动支付逻辑
	// 目前只是等待用户手动完成支付
	log.Println("请在浏览器中手动完成支付...")

	// 等待支付完成
	for i := 0; i < 60; i++ { // 最多等待60秒
		time.Sleep(1 * time.Second)

		// 检查是否支付成功
		success, err := tg.browser.ElementExists(ctx, ".payment-success")
		if err == nil && success {
			log.Println("支付成功！")
			return nil
		}
	}

	return fmt.Errorf("支付超时")
}

// loadConfig 加载配置
func loadConfig(configFile string) (*models.Config, error) {
	data, err := os.ReadFile(configFile)
	if err != nil {
		return nil, err
	}

	var config models.Config
	err = json.Unmarshal(data, &config)
	if err != nil {
		return nil, err
	}

	return &config, nil
}

// findConcertByID 根据ID查找演唱会
func findConcertByID(concerts []models.Concert, id string) *models.Concert {
	for _, concert := range concerts {
		if concert.ID == id {
			return &concert
		}
	}
	return nil
}
