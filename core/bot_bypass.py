import random
import json
from typing import Dict, List, Any, Optional
from selenium import webdriver


class BotBypassManager:
    """
    Advanced bot detection bypass techniques
    """
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
    
    def apply_all_bypasses(self,
                          timezone: str = "Asia/Ho_Chi_Minh",
                          language: str = "vi-VN",
                          geolocation: Dict[str, float] = None):
        """Apply all bot bypass techniques"""

        try:
            self.bypass_webdriver_detection()
        except Exception as e:
            print(f"Warning: webdriver bypass failed: {e}")

        try:
            self.bypass_chrome_detection()
        except Exception as e:
            print(f"Warning: chrome bypass failed: {e}")

        try:
            self.bypass_navigator_properties()
        except Exception as e:
            print(f"Warning: navigator bypass failed: {e}")

        # Skip problematic bypasses for now
        # self.bypass_canvas_fingerprinting()
        # self.bypass_webgl_fingerprinting()
        # self.bypass_audio_fingerprinting()

        try:
            self.set_timezone(timezone)
        except Exception as e:
            print(f"Warning: timezone bypass failed: {e}")

        try:
            self.set_language(language)
        except Exception as e:
            print(f"Warning: language bypass failed: {e}")

        if geolocation:
            try:
                self.set_geolocation(geolocation)
            except Exception as e:
                print(f"Warning: geolocation bypass failed: {e}")
    
    def bypass_webdriver_detection(self):
        """Remove webdriver traces"""

        try:
            # Remove webdriver property (only if it exists)
            self.driver.execute_script("""
                if (navigator.webdriver !== undefined) {
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        configurable: true
                    });
                }
            """)
        except Exception as e:
            print(f"Warning: Could not override webdriver property: {e}")

        try:
            # Remove automation flags
            self.driver.execute_script("""
                if (window.chrome && window.chrome.runtime) {
                    delete window.chrome.runtime.onConnect;
                    delete window.chrome.runtime.onMessage;
                }
            """)
        except Exception as e:
            print(f"Warning: Could not remove chrome runtime: {e}")
    
    def bypass_chrome_detection(self):
        """Bypass Chrome automation detection"""
        
        # Add chrome object if missing
        self.driver.execute_script("""
            if (!window.chrome) {
                window.chrome = {};
            }
            if (!window.chrome.runtime) {
                window.chrome.runtime = {};
            }
        """)
        
        # Override chrome runtime
        self.driver.execute_script("""
            Object.defineProperty(window.chrome.runtime, 'onConnect', {
                value: undefined,
                writable: false
            });
            Object.defineProperty(window.chrome.runtime, 'onMessage', {
                value: undefined,
                writable: false
            });
        """)
    
    def bypass_navigator_properties(self):
        """Override navigator properties to appear more human"""
        
        # Override plugins
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    },
                    {
                        0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: Plugin},
                        1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: Plugin},
                        description: "",
                        filename: "internal-nacl-plugin",
                        length: 2,
                        name: "Native Client"
                    }
                ]
            });
        """)
        
        # Override languages
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['vi-VN', 'vi', 'en-US', 'en']
            });
        """)
        
        # Override permissions
        self.driver.execute_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Override connection
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    downlink: 10,
                    effectiveType: '4g',
                    rtt: 50,
                    saveData: false
                })
            });
        """)
    
    def bypass_canvas_fingerprinting(self):
        """Randomize canvas fingerprinting"""
        
        self.driver.execute_script("""
            const getImageData = HTMLCanvasElement.prototype.getContext('2d').getImageData;
            HTMLCanvasElement.prototype.getContext('2d').getImageData = function(sx, sy, sw, sh) {
                const imageData = getImageData.apply(this, arguments);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                    imageData.data[i + 1] += Math.floor(Math.random() * 10) - 5;
                    imageData.data[i + 2] += Math.floor(Math.random() * 10) - 5;
                }
                return imageData;
            };
        """)
        
        # Override toDataURL
        self.driver.execute_script("""
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = `rgb(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)})`;
                ctx.fillRect(0, 0, 1, 1);
                return toDataURL.apply(this, arguments);
            };
        """)
    
    def bypass_webgl_fingerprinting(self):
        """Randomize WebGL fingerprinting"""
        
        self.driver.execute_script("""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
        """)
        
        # Override WebGL2 as well
        self.driver.execute_script("""
            if (typeof WebGL2RenderingContext !== 'undefined') {
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter2.apply(this, arguments);
                };
            }
        """)
    
    def bypass_audio_fingerprinting(self):
        """Randomize audio context fingerprinting"""
        
        self.driver.execute_script("""
            const audioContext = window.AudioContext || window.webkitAudioContext;
            if (audioContext) {
                const createAnalyser = audioContext.prototype.createAnalyser;
                audioContext.prototype.createAnalyser = function() {
                    const analyser = createAnalyser.apply(this, arguments);
                    const getFloatFrequencyData = analyser.getFloatFrequencyData;
                    analyser.getFloatFrequencyData = function(array) {
                        getFloatFrequencyData.apply(this, arguments);
                        for (let i = 0; i < array.length; i++) {
                            array[i] += Math.random() * 0.1 - 0.05;
                        }
                    };
                    return analyser;
                };
            }
        """)
    
    def set_timezone(self, timezone: str):
        """Set timezone to avoid detection"""
        
        self.driver.execute_script(f"""
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                value: function() {{
                    return {{
                        timeZone: '{timezone}',
                        locale: 'vi-VN',
                        calendar: 'gregory',
                        numberingSystem: 'latn'
                    }};
                }}
            }});
        """)
        
        # Override Date timezone
        self.driver.execute_script(f"""
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {{
                return -420; // GMT+7 for Vietnam
            }};
        """)
    
    def set_language(self, language: str):
        """Set language preferences"""
        
        self.driver.execute_script(f"""
            Object.defineProperty(navigator, 'language', {{
                get: () => '{language}'
            }});
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['{language}', 'vi', 'en-US', 'en']
            }});
        """)
    
    def set_geolocation(self, coords: Dict[str, float]):
        """Set fake geolocation"""
        
        self.driver.execute_script(f"""
            Object.defineProperty(navigator.geolocation, 'getCurrentPosition', {{
                value: function(success, error) {{
                    success({{
                        coords: {{
                            latitude: {coords.get('latitude', 21.0285)},
                            longitude: {coords.get('longitude', 105.8542)},
                            accuracy: 20,
                            altitude: null,
                            altitudeAccuracy: null,
                            heading: null,
                            speed: null
                        }},
                        timestamp: Date.now()
                    }});
                }}
            }});
        """)
    
    def randomize_mouse_movements(self):
        """Add random mouse movements to appear more human"""
        
        self.driver.execute_script("""
            function randomMouseMove() {
                const event = new MouseEvent('mousemove', {
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight,
                    bubbles: true
                });
                document.dispatchEvent(event);
            }
            
            setInterval(randomMouseMove, Math.random() * 5000 + 2000);
        """)
    
    def add_human_behavior_scripts(self):
        """Add scripts that simulate human behavior"""
        
        # Random scrolling
        self.driver.execute_script("""
            function randomScroll() {
                const scrollAmount = Math.random() * 200 - 100;
                window.scrollBy(0, scrollAmount);
            }
            
            setInterval(randomScroll, Math.random() * 10000 + 5000);
        """)
        
        # Random clicks on empty areas
        self.driver.execute_script("""
            function randomClick() {
                if (Math.random() < 0.1) {
                    const x = Math.random() * window.innerWidth;
                    const y = Math.random() * window.innerHeight;
                    const element = document.elementFromPoint(x, y);
                    if (element && element.tagName === 'BODY') {
                        element.click();
                    }
                }
            }
            
            setInterval(randomClick, Math.random() * 30000 + 15000);
        """)
    
    def bypass_headless_detection(self):
        """Bypass headless browser detection"""
        
        # Override headless indicators
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['vi-VN', 'vi']});
            
            window.chrome = {
                runtime: {}
            };
            
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({state: 'granted'})
                })
            });
        """)
        
        # Add missing properties for headless detection
        self.driver.execute_script("""
            if (!window.outerHeight) {
                Object.defineProperty(window, 'outerHeight', {get: () => window.innerHeight});
            }
            if (!window.outerWidth) {
                Object.defineProperty(window, 'outerWidth', {get: () => window.innerWidth});
            }
        """)
