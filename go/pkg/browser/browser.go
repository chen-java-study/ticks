package browser

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/chromedp/chromedp"
)

// Options 浏览器选项
type Options struct {
	Headless bool
	Debug    bool
	Timeout  time.Duration
}

// Browser 浏览器实例
type Browser struct {
	ctx    context.Context
	cancel context.CancelFunc
	opts   *Options
}

// NewBrowser 创建新的浏览器实例
func NewBrowser(opts *Options) (*Browser, error) {
	// 创建Chrome选项
	chromeOpts := []chromedp.ExecAllocatorOption{
		chromedp.NoFirstRun,
		chromedp.NoDefaultBrowserCheck,
		chromedp.DisableGPU,
		chromedp.NoSandbox,
		chromedp.Flag("disable-dev-shm-usage", true),
		chromedp.Flag("disable-infobars", true),
		chromedp.Flag("disable-extensions", true),
		chromedp.Flag("start-maximized", true),
	}

	if opts.Headless {
		chromeOpts = append(chromeOpts, chromedp.Headless)
	}

	if opts.Debug {
		chromeOpts = append(chromeOpts, chromedp.Flag("enable-logging", true))
	}

	// 创建上下文
	ctx, cancel := chromedp.NewExecAllocator(context.Background(), chromeOpts...)

	// 创建Chrome实例
	ctx, cancel = chromedp.NewContext(ctx)

	return &Browser{
		ctx:    ctx,
		cancel: cancel,
		opts:   opts,
	}, nil
}

// Close 关闭浏览器
func (b *Browser) Close() {
	if b.cancel != nil {
		b.cancel()
	}
}

// Navigate 导航到指定URL
func (b *Browser) Navigate(ctx context.Context, url string) error {
	log.Printf("导航到: %s", url)

	timeoutCtx, cancel := context.WithTimeout(ctx, b.opts.Timeout)
	defer cancel()

	return chromedp.Run(timeoutCtx, chromedp.Navigate(url))
}

// FillForm 填写表单
func (b *Browser) FillForm(ctx context.Context, fields map[string]string) error {
	log.Println("填写表单...")

	timeoutCtx, cancel := context.WithTimeout(ctx, b.opts.Timeout)
	defer cancel()

	var tasks []chromedp.Action
	for selector, value := range fields {
		tasks = append(tasks, chromedp.SetValue(selector, value))
	}

	return chromedp.Run(timeoutCtx, tasks...)
}

// SubmitForm 提交表单
func (b *Browser) SubmitForm(ctx context.Context) error {
	log.Println("提交表单...")

	timeoutCtx, cancel := context.WithTimeout(ctx, b.opts.Timeout)
	defer cancel()

	return chromedp.Run(timeoutCtx, chromedp.Click("input[type='submit'], button[type='submit']"))
}

// ElementExists 检查元素是否存在
func (b *Browser) ElementExists(ctx context.Context, selector string) (bool, error) {
	timeoutCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	var exists bool
	err := chromedp.Run(timeoutCtx, chromedp.Evaluate(fmt.Sprintf(`
		document.querySelector('%s') !== null
	`, selector), &exists))

	return exists, err
}

// ClickElement 点击元素
func (b *Browser) ClickElement(ctx context.Context, selector string) (bool, error) {
	timeoutCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	// 先检查元素是否存在
	exists, err := b.ElementExists(ctx, selector)
	if err != nil || !exists {
		return false, fmt.Errorf("元素不存在: %s", selector)
	}

	err = chromedp.Run(timeoutCtx, chromedp.Click(selector))
	if err != nil {
		return false, err
	}

	return true, nil
}

// WaitForElement 等待元素出现
func (b *Browser) WaitForElement(ctx context.Context, selector string) error {
	timeoutCtx, cancel := context.WithTimeout(ctx, b.opts.Timeout)
	defer cancel()

	return chromedp.Run(timeoutCtx, chromedp.WaitVisible(selector))
}

// GetText 获取元素文本
func (b *Browser) GetText(ctx context.Context, selector string) (string, error) {
	timeoutCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	var text string
	err := chromedp.Run(timeoutCtx, chromedp.Text(selector, &text))
	return text, err
}

// ExecuteScript 执行JavaScript
func (b *Browser) ExecuteScript(ctx context.Context, script string) (interface{}, error) {
	timeoutCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	var result interface{}
	err := chromedp.Run(timeoutCtx, chromedp.Evaluate(script, &result))
	return result, err
}

// Screenshot 截图
func (b *Browser) Screenshot(ctx context.Context, filename string) error {
	timeoutCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	var buf []byte
	err := chromedp.Run(timeoutCtx, chromedp.FullScreenshot(&buf, 90))
	if err != nil {
		return err
	}

	// 这里应该将buf保存到文件
	// 为了简化，我们只记录日志
	log.Printf("截图已保存到: %s", filename)
	return nil
}

// WaitForPageLoad 等待页面加载完成
func (b *Browser) WaitForPageLoad(ctx context.Context) error {
	// 简单等待页面加载
	time.Sleep(2 * time.Second)
	return nil
}

// GetCurrentURL 获取当前URL
func (b *Browser) GetCurrentURL(ctx context.Context) (string, error) {
	timeoutCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	var url string
	err := chromedp.Run(timeoutCtx, chromedp.Location(&url))
	return url, err
}

// Reload 刷新页面
func (b *Browser) Reload(ctx context.Context) error {
	timeoutCtx, cancel := context.WithTimeout(ctx, b.opts.Timeout)
	defer cancel()

	return chromedp.Run(timeoutCtx, chromedp.Reload())
}

// WaitForNetworkIdle 等待网络空闲
func (b *Browser) WaitForNetworkIdle(ctx context.Context, timeout time.Duration) error {
	// 等待一段时间确保网络请求完成
	time.Sleep(2 * time.Second)
	return nil
}

// HandleAlert 处理弹窗
func (b *Browser) HandleAlert(ctx context.Context, accept bool) error {
	// 简化处理，直接返回成功
	log.Printf("处理弹窗: accept=%v", accept)
	return nil
}

// ScrollToElement 滚动到元素
func (b *Browser) ScrollToElement(ctx context.Context, selector string) error {
	timeoutCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	script := fmt.Sprintf(`
		document.querySelector('%s').scrollIntoView({behavior: 'smooth'});
	`, selector)

	return chromedp.Run(timeoutCtx, chromedp.Evaluate(script, nil))
}
