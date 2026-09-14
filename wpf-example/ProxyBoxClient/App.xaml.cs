using System;
using System.Windows;

namespace ProxyBoxClient
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            
            // Set default API base URL if not configured
            // Can be overridden in settings
        }
    }
}
