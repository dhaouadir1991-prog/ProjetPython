// Get public IP address
async function getPublicIP() {
  try {
    const response = await fetch("https://api.ipify.org?format=json");
    const data = await response.json();
    return data.ip;
  } catch (error) {
    console.warn("Could not fetch public IP:", error);
    return null;
  }
}

// Device information collector
async function getDeviceInfo() {
  const publicIP = await getPublicIP();
  
  return {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    languages: navigator.languages,
    screenWidth: window.screen.width,
    screenHeight: window.screen.height,
    screenColorDepth: window.screen.colorDepth,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    hardwareConcurrency: navigator.hardwareConcurrency,
    deviceMemory: navigator.deviceMemory,
    maxTouchPoints: navigator.maxTouchPoints,
    onLine: navigator.onLine,
    publicIP: publicIP,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    title: document.title
  };
}

// Export function
window.getDeviceInfo = getDeviceInfo;
