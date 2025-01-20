/**
 * Browser Automation Task Sequences
 * 
 * This file defines task sequences for browser automation using the browser-use command.
 * Each sequence represents a series of browser interactions that can be executed in order.
 */

export interface BrowserCommand {
    prompt: string;
    url: string;
    provider?: 'Deepseek' | 'Google' | 'OpenAI' | 'Anthropic';
    modelIndex?: number;
    headless?: boolean;
    vision?: boolean;
    record?: boolean;
    recordPath?: string;
    tracePath?: string;
    maxSteps?: number;
    maxActions?: number;
    addInfo?: string;
    windowSize?: string;
    userDataDir?: string;
    proxy?: string;
}

export interface BrowserTask {
    description: string;
    command: BrowserCommand;
    subtasks?: BrowserTask[];
}

export interface BrowserTaskSequence {
    name: string;
    description: string;
    tasks: BrowserTask[];
}

// Example task sequences
export const browserTasks: BrowserTaskSequence[] = [
    {
        name: "Product Research",
        description: "Compare product prices across multiple e-commerce sites",
        tasks: [
            {
                description: "Search Amazon for wireless earbuds",
                command: {
                    prompt: "search for 'wireless earbuds' and tell me the price of the top 3 results",
                    url: "https://www.amazon.com",
                    provider: "Deepseek"
                }
            },
            {
                description: "Search Best Buy for comparison",
                command: {
                    prompt: "search for 'wireless earbuds' and tell me the price of the top 3 results",
                    url: "https://www.bestbuy.com",
                    provider: "Deepseek"
                }
            },
            {
                description: "Create price comparison",
                command: {
                    prompt: "create a comparison table of the prices from both sites",
                    url: "about:blank",
                    provider: "Deepseek"
                }
            }
        ]
    },
    {
        name: "Site Health Check",
        description: "Monitor website availability and performance",
        tasks: [
            {
                description: "Check main site",
                command: {
                    prompt: "check if it loads properly",
                    url: "https://example.com",
                    provider: "Deepseek",
                    headless: true
                }
            },
            {
                description: "Verify API health",
                command: {
                    prompt: "check the API health status",
                    url: "https://api.example.com/health",
                    provider: "Deepseek",
                    headless: true
                }
            },
            {
                description: "Test documentation site",
                command: {
                    prompt: "verify all navigation links are working",
                    url: "https://docs.example.com",
                    provider: "Deepseek",
                    headless: true
                }
            }
        ]
    },
    {
        name: "Content Analysis",
        description: "Analyze blog content and engagement",
        tasks: [
            {
                description: "List articles",
                command: {
                    prompt: "list all article titles from the homepage",
                    url: "https://blog.example.com",
                    provider: "Deepseek"
                }
            },
            {
                description: "Analyze first article",
                command: {
                    prompt: "click on the first article and summarize its main points",
                    url: "https://blog.example.com",
                    provider: "Deepseek"
                },
                subtasks: [
                    {
                        description: "Get metadata",
                        command: {
                            prompt: "tell me the author, publication date, and reading time",
                            url: "https://blog.example.com",
                            provider: "Deepseek"
                        }
                    },
                    {
                        description: "Analyze comments",
                        command: {
                            prompt: "scroll to the comments section and summarize the main discussion points",
                            url: "https://blog.example.com",
                            provider: "Deepseek"
                        }
                    }
                ]
            }
        ]
    },
    {
        name: "Advanced Content Analysis",
        description: "Analyze website content using different models for different tasks",
        tasks: [
            {
                description: "Initial navigation and basic text extraction",
                command: {
                    prompt: "navigate to the Actions documentation and extract basic text content",
                    url: "https://docs.github.com",
                    provider: "Deepseek"
                }
            },
            {
                description: "Visual analysis of page structure",
                command: {
                    prompt: "analyze the layout of the page and tell me how the documentation is structured, including sidebars, navigation, and content areas",
                    url: "https://docs.github.com",
                    provider: "Google",
                    vision: true,
                    modelIndex: 1,
                    addInfo: "Only using Google here because we need vision capabilities"
                }
            },
            {
                description: "Complex content summarization",
                command: {
                    prompt: "summarize the key concepts of GitHub Actions based on the documentation",
                    url: "https://docs.github.com",
                    provider: "Deepseek"
                }
            },
            {
                description: "Extract code examples",
                command: {
                    prompt: "find and list all YAML workflow examples on the page",
                    url: "https://docs.github.com",
                    provider: "Deepseek"
                }
            }
        ]
    },
    {
        name: "Page Structure Analysis",
        description: "Generate detailed reports about page structure and interactive elements",
        tasks: [
            {
                description: "Analyze homepage structure",
                command: {
                    prompt: "create a report about the page structure, including the page title, headings, and any interactive elements found",
                    url: "https://example.com",
                    provider: "Deepseek"
                }
            },
            {
                description: "Analyze navigation structure",
                command: {
                    prompt: "focus on the navigation menu and create a detailed report of its structure and all available links",
                    url: "https://example.com",
                    provider: "Google",
                    vision: true,
                    addInfo: "Only using Google here because we need vision capabilities for complex layout analysis"
                }
            },
            {
                description: "Document forms and inputs",
                command: {
                    prompt: "find all forms on the page and document their inputs, buttons, and validation requirements",
                    url: "https://example.com",
                    provider: "Google",
                    vision: true,
                    addInfo: "Only using Google here because we need vision capabilities for form analysis"
                }
            }
        ]
    },
    {
        name: "Debug Session",
        description: "Record and analyze browser interactions for debugging",
        tasks: [
            {
                description: "Start debug session",
                command: {
                    prompt: "attempt to log in with test credentials",
                    url: "https://example.com/login",
                    provider: "Deepseek",
                    headless: false,
                    tracePath: "./tmp/traces/login",
                    record: true,
                    recordPath: "./recordings/login"
                }
            },
            {
                description: "Navigate complex workflow",
                command: {
                    prompt: "complete the multi-step registration process",
                    url: "https://example.com/register",
                    provider: "Deepseek",
                    maxSteps: 5,
                    maxActions: 2,
                    tracePath: "./tmp/traces/registration"
                }
            },
            {
                description: "Generate debug report",
                command: {
                    prompt: "create a report of all actions taken and any errors encountered",
                    url: "about:blank",
                    provider: "Deepseek",
                    addInfo: "Focus on error patterns and user interaction points"
                }
            }
        ]
    }
];

// Updated execute task function to match CLI arguments
const executeTask = (task: BrowserCommand): string => {
    const options: string[] = [];
    
    if (task.provider) options.push(`--provider ${task.provider}`);
    if (task.modelIndex !== undefined) options.push(`--model-index ${task.modelIndex}`);
    if (task.headless) options.push('--headless');
    if (task.vision) options.push('--vision');
    if (task.record) {
        options.push('--record');
        if (task.recordPath) options.push(`--record-path ${task.recordPath}`);
    }
    if (task.tracePath) options.push(`--trace-path ${task.tracePath}`);
    if (task.maxSteps) options.push(`--max-steps ${task.maxSteps}`);
    if (task.maxActions) options.push(`--max-actions ${task.maxActions}`);
    if (task.addInfo) options.push(`--add-info "${task.addInfo}"`);
    if (task.windowSize) options.push(`--window-size ${task.windowSize}`);
    if (task.userDataDir) options.push(`--user-data-dir "${task.userDataDir}"`);
    if (task.proxy) options.push(`--proxy "${task.proxy}"`);
    
    return `browser-use run "${task.prompt}" --url "${task.url}" ${options.join(' ')}`.trim();
};

// Example usage:
const sequence = browserTasks[0]; // Get Product Research sequence
console.log(`Executing sequence: ${sequence.name}`);
sequence.tasks.forEach(task => {
    console.log(`\n${task.description}:`);
    console.log(executeTask(task.command));
}); 