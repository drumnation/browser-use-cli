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
    keepSessionAlive?: boolean;
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
                    vision: true,
                    keepSessionAlive: true
                }
            },
            {
                description: "Search Best Buy for comparison",
                command: {
                    prompt: "go to bestbuy.com and search for 'wireless earbuds' and tell me the price of the top 3 results",
                    model: "gemini",
                    vision: true,
                    keepSessionAlive: true
                }
            },
            {
                description: "Create price comparison",
                command: {
                    prompt: "create a comparison table of the prices from both sites",
                    keepSessionAlive: false
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
                    keepSessionAlive: true
                }
            },
            {
                description: "Visual analysis of page structure",
                command: {
                    prompt: "analyze the layout of the page and tell me how the documentation is structured, including sidebars, navigation, and content areas",
                    model: "gemini",  // Switch to Gemini for visual analysis
                    vision: true,
                    keepSessionAlive: true
                }
            },
            {
                description: "Complex content summarization",
                command: {
                    prompt: "summarize the key concepts of GitHub Actions based on the documentation",
                    model: "claude-3",  // Switch to Claude for complex summarization
                    keepSessionAlive: true
                }
            },
            {
                description: "Extract code examples",
                command: {
                    prompt: "find and list all YAML workflow examples on the page",
                    model: "deepseek-chat",  // Back to DeepSeek for code extraction
                    keepSessionAlive: false  // Close browser after final task
                }
            }
        ]
    }
];

// Example of executing a task sequence
const executeTask = (task: BrowserCommand): string => {
    const options: string[] = [];
    if (task.model) options.push(`--model ${task.model}`);
    if (task.headless) options.push('--headless');
    if (task.vision) options.push('--vision');
    if (task.keepSessionAlive) options.push('--keep-browser-open');
    
    return `browser-use "${task.prompt}" ${options.join(' ')}`.trim();
};

// Example usage:
const sequence = browserTasks[0]; // Get Product Research sequence
console.log(`Executing sequence: ${sequence.name}`);
sequence.tasks.forEach(task => {
    console.log(`\n${task.description}:`);
    console.log(executeTask(task.command));
}); 