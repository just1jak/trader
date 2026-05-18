// Sample data for demonstration - in a real implementation, this would come from an API or data source
const projects = [
    {
        id: 1,
        name: "Smart Money Tracker",
        description": "Financial risk scoring system (currently V5.1)",
        progress: 75,
        status: "active",
        tags: ["finance", "risk-scoring", "n8n"]
    },
    {
        id: 2,
        name: "Parkwood Accord",
        description": "iOS app for couples spending",
        progress: 60,
        status: "active",
        tags: ["ios", "couples", "swift"]
    },
    {
        id: 3,
        name: "A-Liner Replication",
        description": "DIY hard-sided pop-up camper build",
        progress: 40,
        status: "planning",
        tags: ["diY", "camping", "engineering"]
    },
    {
        id: 4,
        name: "CampingSniper",
        description": "Campsite availability monitor hitting Recreation.gov's internal API",
        progress: 90,
        status: "active",
        tags: ["automation", "recreation.gov", "slack-bot"]
    },
    {
        id: 5,
        name: "Paper Trading",
        description": "Futures paper trading via Tradovate API integration in n8n",
        progress: 80,
        status: "active",
        tags: ["trading", "tradovate", "n8n"]
    },
    {
        id: 6,
        name: "STEM with Roo",
        description": "Children's STEM education content brand",
        progress: 50,
        status: "planning",
        tags: ["education", "content", "children"]
    },
    {
        id: 7,
        name: "iOS Apps Suite",
        description": "Pill counting app + CleanStreak habit tracker",
        progress: 55,
        status: "active",
        tags: ["ios", "health", "habit-tracking"]
    },
    {
        id: 8,
        name: "Self-hosting Course",
        description": "Potential digital product — Proxmox-based self-hosting education",
        progress: 20,
        status: "planning",
        tags: ["education", "proxmox", "self-hosting"]
    }
];

const metrics = [
    {
        label: "Projects Active",
        value: "5/8",
        description: "Currently in development"
    },
    {
        label: "Progress Overall",
        value: "58%",
        description: "Average completion across all projects"
    },
    {
        label: "Time Invested",
        value: "120+ hrs",
        description: "Estimated development time"
    },
    {
        label: "Next Milestone",
        value: "Q3 2026",
        description: "Public-facing version target"
    }
];

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
    renderProjects();
    renderMetrics();
});

// Render project cards
function renderProjects() {
    const projectList = document.querySelector('.project-list');
    
    projects.forEach(project => {
        const projectCard = document.createElement('div');
        projectCard.className = 'project-card';
        projectCard.innerHTML = `
            <div class="project-header">
                <h3>${project.name}</h3>
                <div class="tags">
                    ${project.tags.map(tag => `<span>${tag}</span>`).join('')}
                </div>
            </div>
            <div class="project-body">
                <p>${project.description}</p>
                <div class="progress">
                    <div style="width: ${project.progress}%"></div>
                </div>
                <p><strong>Progress:</strong> ${project.progress}%</p>
            </div>
            <div class="project-footer">
                <span class="status ${project.status}">${project.status.toUpperCase()}</span>
                <span>Updated: ${new Date().toLocaleDateString()}</span>
            </div>
        `;
        projectList.appendChild(projectCard);
    });
}

// Render metrics cards
function renderMetrics() {
    const metricsGrid = document.querySelector('.metrics-grid');
    
    metrics.forEach(metric => {
        const metricCard = document.createElement('div');
        metricCard.className = 'metric-card';
        metricCard.innerHTML = `
            <h3>${metric.label}</h3>
            <div class="value">${metric.value}</div>
            <div class="label">${metric.description}</div>
        `;
        metricsGrid.appendChild(metricCard);
    });
}