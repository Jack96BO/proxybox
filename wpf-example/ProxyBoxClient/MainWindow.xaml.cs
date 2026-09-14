using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.ComponentModel;
using System.Windows.Controls;

namespace ProxyBoxClient
{
    public partial class MainWindow : Window, INotifyPropertyChanged
    {
        private readonly HttpClient _httpClient;
        private int _currentPageId = -1;
        
        public MainWindow()
        {
            InitializeComponent();
            DataContext = this;
            _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
            ApiBaseUrl = "http://localhost:5000";
            Pages = new List<PageInfo>();
            TestConnection();
        }
        
        // Properties for data binding
        private string _currentUrl = "http://ilmiosito.com";
        public string CurrentUrl { get => _currentUrl; set { _currentUrl = value; OnPropertyChanged(); } }
        
        private string _javaScriptCode = "// Enter JavaScript code here\nconsole.log('Hello from ProxyBox!');";
        public string JavaScriptCode { get => _javaScriptCode; set { _javaScriptCode = value; OnPropertyChanged(); } }
        
        private string _selector = "input";
        public string Selector { get => _selector; set { _selector = value; OnPropertyChanged(); } }
        
        private string _value = "test";
        public string Value { get => _value; set { _value = value; OnPropertyChanged(); } }
        
        private string _apiBaseUrl = "http://localhost:5000";
        public string ApiBaseUrl { get => _apiBaseUrl; set { _apiBaseUrl = value; OnPropertyChanged(); } }
        
        private string _apiStatus = "Disconnected";
        public string ApiStatus { get => _apiStatus; set { _apiStatus = value; OnPropertyChanged(); } }
        
        private SolidColorBrush _apiStatusColor = Brushes.Red;
        public SolidColorBrush ApiStatusColor { get => _apiStatusColor; set { _apiStatusColor = value; OnPropertyChanged(); } }
        
        private string _browserStatus = "Not running";
        public string BrowserStatus { get => _browserStatus; set { _browserStatus = value; OnPropertyChanged(); } }
        
        private SolidColorBrush _browserStatusColor = Brushes.Red;
        public SolidColorBrush BrowserStatusColor { get => _browserStatusColor; set { _browserStatusColor = value; OnPropertyChanged(); } }
        
        private string _statusMessage = "Ready";
        public string StatusMessage { get => _statusMessage; set { _statusMessage = value; OnPropertyChanged(); } }
        
        private ImageSource _screenshotImage;
        public ImageSource ScreenshotImage { get => _screenshotImage; set { _screenshotImage = value; OnPropertyChanged(); } }
        
        private string _htmlContent = "";
        public string HtmlContent { get => _htmlContent; set { _htmlContent = value; OnPropertyChanged(); } }
        
        private string _textContent = "";
        public string TextContent { get => _textContent; set { _textContent = value; OnPropertyChanged(); } }
        
        private Visibility _htmlContentVisibility = Visibility.Collapsed;
        public Visibility HtmlContentVisibility { get => _htmlContentVisibility; set { _htmlContentVisibility = value; OnPropertyChanged(); } }
        
        private Visibility _textContentVisibility = Visibility.Collapsed;
        public Visibility TextContentVisibility { get => _textContentVisibility; set { _textContentVisibility = value; OnPropertyChanged(); } }
        
        private List<PageInfo> _pages;
        public List<PageInfo> Pages { get => _pages; set { _pages = value; OnPropertyChanged(); } }
        
        public PageInfo SelectedPage
        {
            get => _currentPageId > 0 ? Pages.Find(p => p.PageId == _currentPageId) : null;
            set
            {
                if (value != null)
                {
                    _currentPageId = value.PageId;
                    CurrentUrl = value.Url;
                    OnPropertyChanged();
                }
            }
        }
        
        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged([System.Runtime.CompilerServices.CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
        
        // Commands
        public ICommand NewPageCommand => new RelayCommand(_ => NewPage());
        public ICommand ScreenshotCommand => new RelayCommand(_ => TakeScreenshot());
        public ICommand ReloadCommand => new RelayCommand(_ => ReloadPage());
        public ICommand GetHtmlCommand => new RelayCommand(_ => GetHtmlContent());
        public ICommand GetTextCommand => new RelayCommand(_ => GetTextContent());
        public ICommand NavigateCommand => new RelayCommand(_ => Navigate());
        public ICommand BackCommand => new RelayCommand(_ => GoBack());
        public ICommand ForwardCommand => new RelayCommand(_ => GoForward());
        public ICommand ExecuteJsCommand => new RelayCommand(_ => ExecuteJavaScript());
        public ICommand ClickCommand => new RelayCommand(_ => ClickElement());
        public ICommand FillCommand => new RelayCommand(_ => FillForm());
        public ICommand TestConnectionCommand => new RelayCommand(_ => TestConnection());
        
        private async void TestConnection()
        {
            try
            {
                StatusMessage = "Testing connection...";
                var response = await _httpClient.GetAsync($"{ApiBaseUrl}/api/health");
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JsonSerializer.Deserialize<JsonElement>(content);
                    
                    ApiStatus = "Connected";
                    ApiStatusColor = Brushes.Green;
                    
                    if (json.TryGetProperty("browser", out var browserProp))
                    {
                        BrowserStatus = browserProp.GetBoolean() ? "Running" : "Stopped";
                        BrowserStatusColor = browserProp.GetBoolean() ? Brushes.Green : Brushes.Red;
                    }
                    
                    StatusMessage = "Connected to ProxyBox API";
                    await RefreshPagesList();
                }
                else
                {
                    ApiStatus = "Error";
                    ApiStatusColor = Brushes.Red;
                    BrowserStatus = "Error";
                    BrowserStatusColor = Brushes.Red;
                    StatusMessage = $"API Error: {response.StatusCode}";
                }
            }
            catch (Exception ex)
            {
                ApiStatus = "Disconnected";
                ApiStatusColor = Brushes.Red;
                BrowserStatus = "Not running";
                BrowserStatusColor = Brushes.Red;
                StatusMessage = $"Connection failed: {ex.Message}";
            }
        }
        
        private async void NewPage()
        {
            try
            {
                StatusMessage = "Creating new page...";
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/create", null);
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JsonSerializer.Deserialize<JsonElement>(content);
                    _currentPageId = json.GetProperty("page_id").GetInt32();
                    StatusMessage = "New page created";
                    await RefreshPagesList();
                }
                else
                {
                    StatusMessage = "Failed to create page";
                }
            }
            catch (Exception ex)
            {
                StatusMessage = $"Error: {ex.Message}";
            }
        }
        
        private async void Navigate()
        {
            if (_currentPageId <= 0) await NewPage();
            if (_currentPageId <= 0 || string.IsNullOrEmpty(CurrentUrl)) return;
            
            try
            {
                StatusMessage = "Navigating...";
                var requestContent = new { url = CurrentUrl };
                var jsonContent = new StringContent(JsonSerializer.Serialize(requestContent), Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/navigate", jsonContent);
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JsonSerializer.Deserialize<JsonElement>(content);
                    StatusMessage = "Navigation completed";
                    if (json.TryGetProperty("url", out var urlProp)) CurrentUrl = urlProp.GetString();
                    await RefreshPagesList();
                }
                else StatusMessage = "Navigation failed";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void TakeScreenshot()
        {
            if (_currentPageId <= 0) return;
            try
            {
                StatusMessage = "Taking screenshot...";
                var requestContent = new { format = "png", full_page = true };
                var jsonContent = new StringContent(JsonSerializer.Serialize(requestContent), Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/screenshot", jsonContent);
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JsonSerializer.Deserialize<JsonElement>(content);
                    if (json.TryGetProperty("image", out var imageProp))
                    {
                        var imageBytes = Convert.FromBase64String(imageProp.GetString());
                        using (var ms = new MemoryStream(imageBytes))
                        {
                            var bitmap = new BitmapImage();
                            bitmap.BeginInit();
                            bitmap.StreamSource = ms;
                            bitmap.CacheOption = BitmapCacheOption.OnLoad;
                            bitmap.EndInit();
                            bitmap.Freeze();
                            ScreenshotImage = bitmap;
                        }
                    }
                    StatusMessage = "Screenshot captured";
                    HtmlContentVisibility = Visibility.Collapsed;
                    TextContentVisibility = Visibility.Collapsed;
                }
                else StatusMessage = "Failed to capture screenshot";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void GetHtmlContent()
        {
            if (_currentPageId <= 0) return;
            try
            {
                StatusMessage = "Getting HTML content...";
                var response = await _httpClient.GetAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/content");
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JsonSerializer.Deserialize<JsonElement>(content);
                    if (json.TryGetProperty("content", out var contentProp)) HtmlContent = contentProp.GetString();
                    StatusMessage = "HTML content loaded";
                    HtmlContentVisibility = Visibility.Visible;
                    TextContentVisibility = Visibility.Collapsed;
                    ScreenshotImage = null;
                }
                else StatusMessage = "Failed to get HTML content";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void GetTextContent()
        {
            if (_currentPageId <= 0) return;
            try
            {
                StatusMessage = "Getting text content...";
                var response = await _httpClient.GetAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/text");
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JsonSerializer.Deserialize<JsonElement>(content);
                    if (json.TryGetProperty("text", out var textProp)) TextContent = textProp.GetString();
                    StatusMessage = "Text content loaded";
                    HtmlContentVisibility = Visibility.Collapsed;
                    TextContentVisibility = Visibility.Visible;
                    ScreenshotImage = null;
                }
                else StatusMessage = "Failed to get text content";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void ReloadPage()
        {
            if (_currentPageId <= 0) return;
            try
            {
                StatusMessage = "Reloading page...";
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/reload", null);
                StatusMessage = response.IsSuccessStatusCode ? "Page reloaded" : "Failed to reload page";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void GoBack()
        {
            if (_currentPageId <= 0) return;
            try
            {
                StatusMessage = "Going back...";
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/back", null);
                StatusMessage = response.IsSuccessStatusCode ? "Went back" : "Failed to go back";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void GoForward()
        {
            if (_currentPageId <= 0) return;
            try
            {
                StatusMessage = "Going forward...";
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/forward", null);
                StatusMessage = response.IsSuccessStatusCode ? "Went forward" : "Failed to go forward";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void ExecuteJavaScript()
        {
            if (_currentPageId <= 0 || string.IsNullOrEmpty(JavaScriptCode)) return;
            try
            {
                StatusMessage = "Executing JavaScript...";
                var requestContent = new { script = JavaScriptCode };
                var jsonContent = new StringContent(JsonSerializer.Serialize(requestContent), Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/execute", jsonContent);
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JsonSerializer.Deserialize<JsonElement>(content);
                    StatusMessage = json.TryGetProperty("result", out var resultProp) ? $"JS Result: {resultProp.GetRawText()}" : "JavaScript executed";
                }
                else StatusMessage = "Failed to execute JavaScript";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void ClickElement()
        {
            if (_currentPageId <= 0 || string.IsNullOrEmpty(Selector)) return;
            try
            {
                StatusMessage = "Clicking element...";
                var requestContent = new { selector = Selector };
                var jsonContent = new StringContent(JsonSerializer.Serialize(requestContent), Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/click", jsonContent);
                StatusMessage = response.IsSuccessStatusCode ? "Element clicked" : "Click failed";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void FillForm()
        {
            if (_currentPageId <= 0 || string.IsNullOrEmpty(Selector)) return;
            try
            {
                StatusMessage = "Filling form...";
                var requestContent = new { selector = Selector, value = Value };
                var jsonContent = new StringContent(JsonSerializer.Serialize(requestContent), Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync($"{ApiBaseUrl}/api/page/{_currentPageId}/fill", jsonContent);
                StatusMessage = response.IsSuccessStatusCode ? "Form filled" : "Failed to fill form";
            }
            catch (Exception ex) { StatusMessage = $"Error: {ex.Message}"; }
        }
        
        private async void RefreshPagesList()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{ApiBaseUrl}/api/pages/list");
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JsonSerializer.Deserialize<JsonElement>(content);
                    if (json.TryGetProperty("pages", out var pagesProp))
                    {
                        var newPages = new List<PageInfo>();
                        foreach (var pageJson in pagesProp.EnumerateArray())
                        {
                            newPages.Add(new PageInfo
                            {
                                PageId = pageJson.GetProperty("page_id").GetInt32(),
                                Title = pageJson.GetProperty("title").GetString(),
                                Url = pageJson.GetProperty("url").GetString()
                            });
                        }
                        Pages = newPages;
                    }
                }
            }
            catch (Exception ex) { StatusMessage = $"Error refreshing pages: {ex.Message}"; }
        }
        
        private void UrlTextBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter) { Navigate(); e.Handled = true; }
        }
        
        protected override void OnClosed(EventArgs e)
        {
            _httpClient.Dispose();
            base.OnClosed(e);
        }
    }
    
    public class PageInfo
    {
        public int PageId { get; set; }
        public string Title { get; set; }
        public string Url { get; set; }
    }
    
    public class RelayCommand : ICommand
    {
        private readonly Action<object> _execute;
        private readonly Predicate<object> _canExecute;
        
        public RelayCommand(Action<object> execute, Predicate<object> canExecute = null)
        {
            _execute = execute ?? throw new ArgumentNullException(nameof(execute));
            _canExecute = canExecute;
        }
        
        public bool CanExecute(object parameter) => _canExecute?.Invoke(parameter) ?? true;
        public void Execute(object parameter) => _execute(parameter);
        
        public event EventHandler CanExecuteChanged
        {
            add => CommandManager.RequerySuggested += value;
            remove => CommandManager.RequerySuggested -= value;
        }
    }
}
