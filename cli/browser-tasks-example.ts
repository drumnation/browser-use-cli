/**
 * Browser Automation Task Sequences
 * 
 * This file defines task sequences for browser automation using the browser-use command.
 * Each sequence represents a series of browser interactions that can be executed in order.
 */

export interface BrowserCommand {
    prompt: string;
    model?: 'deepseek-chat' | 'gemini' | 'gpt-4' | 'claude-3';
    headless?: boolean;
    vision?: boolean;
    record?: boolean;
    recordPath?: string;
    tracePath?: string;
    maxSteps?: number;
    maxActions?: number;
    addInfo?: string;
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
                    prompt: "go to amazon.com and search for 'wireless earbuds' and tell me the price of the top 3 results",
                    model: "gemini",
                    vision: true
                }
            },
            {
                description: "Search Best Buy for comparison",
                command: {
                    prompt: "go to bestbuy.com and search for 'wireless earbuds' and tell me the price of the top 3 results",
                    model: "gemini",
                    vision: true
                }
            },
            {
                description: "Create price comparison",
                command: {
                    prompt: "create a comparison table of the prices from both sites"
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
                    prompt: "go to example.com and check if it loads properly",
                    headless: true
                }
            },
            {
                description: "Verify API health",
                command: {
                    prompt: "go to api.example.com/health and tell me the status",
                    headless: true
                }
            },
            {
                description: "Test documentation site",
                command: {
                    prompt: "go to docs.example.com and verify all navigation links are working",
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
                    prompt: "go to blog.example.com and list all article titles from the homepage",
                    model: "gemini",
                    vision: true
                }
            },
            {
                description: "Analyze first article",
                command: {
                    prompt: "click on the first article and summarize its main points"
                },
                subtasks: [
                    {
                        description: "Get metadata",
                        command: {
                            prompt: "tell me the author, publication date, and reading time"
                        }
                    },
                    {
                        description: "Analyze comments",
                        command: {
                            prompt: "scroll to the comments section and summarize the main discussion points",
                            vision: true
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
                    prompt: "go to docs.github.com and navigate to the Actions documentation",
                    model: "deepseek-chat",  // Use DeepSeek for basic navigation
                }
            },
            {
                description: "Visual analysis of page structure",
                command: {
                    prompt: "analyze the layout of the page and tell me how the documentation is structured, including sidebars, navigation, and content areas",
                    model: "gemini",  // Switch to Gemini for visual analysis
                    vision: true,
                }
            },
            {
                description: "Complex content summarization",
                command: {
                    prompt: "summarize the key concepts of GitHub Actions based on the documentation",
                    model: "claude-3",  // Switch to Claude for complex summarization
                }
            },
            {
                description: "Extract code examples",
                command: {
                    prompt: "find and list all YAML workflow examples on the page",
                    model: "deepseek-chat",  // Back to DeepSeek for code extraction
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
                    prompt: "go to example.com and create a report about the page structure, including the page title, headings, and any interactive elements found",
                    model: "gemini",
                    vision: true,
                }
            },
            {
                description: "Analyze navigation structure",
                command: {
                    prompt: "focus on the navigation menu and create a detailed report of its structure and all available links",
                    model: "gemini",
                    vision: true,
                }
            },
            {
                description: "Document forms and inputs",
                command: {
                    prompt: "find all forms on the page and document their inputs, buttons, and validation requirements",
                    model: "gemini",
                    vision: true
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
                    prompt: "go to example.com/login and attempt to log in with test credentials",
                    model: "deepseek-chat",
                    headless: false,
                    tracePath: "./tmp/traces/login"
                }
            },
            {
                description: "Navigate complex workflow",
                command: {
                    prompt: "complete the multi-step registration process",
                    model: "deepseek-chat",
                    tracePath: "./tmp/traces/registration"
                }
            },
            {
                description: "Generate debug report",
                command: {
                    prompt: "create a report of all actions taken and any errors encountered",
                    model: "claude-3",
                    tracePath: "./tmp/traces/report"
                }
            }
        ]
    }
];

// Updated execute task function to match CLI arguments
const executeTask = (task: BrowserCommand): string => {
    const options: string[] = [];
    
    if (task.model) options.push(`--model ${task.model}`);
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
    
    return `browser-use run "${task.prompt}" ${options.join(' ')}`.trim();
};

// Example usage:
const sequence = browserTasks[0]; // Get Product Research sequence
console.log(`Executing sequence: ${sequence.name}`);
sequence.tasks.forEach(task => {
    console.log(`\n${task.description}:`);
    console.log(executeTask(task.command));
}); 