// 大模型请求测试工具 - 前端逻辑

// 全局变量存储系统提示词
let SYSTEM_PROMPT = "加载中...";

// 异步获取系统提示词
async function loadSystemPrompt() {
    try {
        const response = await fetch('/system-prompt');
        const data = await response.json();
        SYSTEM_PROMPT = data.system_prompt;
        console.log('系统提示词已加载');
    } catch (error) {
        console.error('获取系统提示词失败:', error);
        SYSTEM_PROMPT = "默认系统提示词";
    }
}

// 异步获取默认模型
async function loadDefaultModel() {
    try {
        const response = await fetch('/default-model');
        const data = await response.json();
        const modelInput = document.getElementById('model');
        if (modelInput) {
            modelInput.value = data.default_model;
        }
        console.log('默认模型已加载:', data.default_model);
        return data.default_model;
    } catch (error) {
        console.error('获取默认模型失败:', error);
        return 'qwen3-coder-plus'; // 回退默认值
    }
}

class LLMTester {
    constructor() {
        this.currentSessionId = null;
        this.isRunning = false;
    }

    static async create() {
        const instance = new LLMTester();
        await instance.init();
        return instance;
    }

    async init() {
        // 先加载系统提示词和默认模型
        await loadSystemPrompt();
        const defaultModel = await loadDefaultModel();
        
        this.bindEvents();
        this.loadSessions();
        await this.setDefaultPrompt(defaultModel);
        this.toggleRequestMode(); // 默认显示简单模式
    }

    async setDefaultPrompt(defaultModel = 'qwen3-coder-plus') {
        // 简单模式默认内容已在HTML中设置
        
        // 设置JSON模式的默认内容
        const defaultJsonRequest = {
            "model": defaultModel,
            "messages": [
                {
                    "role": "user",
                    "content": "你好，请介绍一下你自己。"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        };
        
        document.getElementById('requestJson').value = JSON.stringify(defaultJsonRequest, null, 2);
    }

    bindEvents() {
        console.log('绑定事件...');
        
        // 绑定表单提交事件
        const testForm = document.getElementById('testForm');
        if (testForm) {
            console.log('找到测试表单，绑定提交事件');
            testForm.addEventListener('submit', (e) => {
                console.log('表单提交事件被触发');
                e.preventDefault();
                this.startTest();
            });
        } else {
            console.error('未找到测试表单元素');
        }

        // 绑定模式切换事件
        document.querySelectorAll('input[name="requestMode"]').forEach(radio => {
            radio.addEventListener('change', () => this.toggleRequestMode());
        });

        // 绑定刷新和清空按钮
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadSessions());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearAllSessions());
    }

    toggleRequestMode() {
        const isSimpleMode = document.getElementById('simpleMode').checked;
        const isJsonMode = document.getElementById('jsonMode').checked;
        
        const simpleModePanel = document.getElementById('simpleModePanel');
        const jsonModePanel = document.getElementById('jsonModePanel');
        
        if (isSimpleMode) {
            simpleModePanel.style.display = 'block';
            jsonModePanel.style.display = 'none';
        } else if (isJsonMode) {
            jsonModePanel.style.display = 'block';
            simpleModePanel.style.display = 'none';
        }
    }

    async startTest() {
        console.log('startTest 方法被调用');
        
        if (this.isRunning) {
            console.log('测试已在运行中，跳过');
            return;
        }
        
        console.log('开始执行测试...');
        this.isRunning = true;
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 测试中...';
        
        try {
            console.log('获取表单数据...');
            const formData = this.getFormData();
            console.log('表单数据:', formData);
            
            // 发送测试请求
            console.log('发送API请求...');
            const response = await fetch('/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            console.log('API响应状态:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('API响应结果:', result);
            this.currentSessionId = result.session_id;
            
            // 开始轮询结果
            this.pollResults();
            
        } catch (error) {
            console.error('测试失败:', error);
            this.showError('测试失败: ' + error.message);
        } finally {
            this.isRunning = false;
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-play-fill"></i> 开始测试';
        }
    }

    getFormData() {
        const isSimpleMode = document.getElementById('simpleMode').checked;
        const isJsonMode = document.getElementById('jsonMode').checked;
        
        const count = parseInt(document.getElementById('count').value);
        
        if (isSimpleMode) {
            // 简单模式：构建基本请求
            const prompt = document.getElementById('prompt').value;
            const model = document.getElementById('model').value;
            const temperature = parseFloat(document.getElementById('temperature').value);
            const maxTokens = parseInt(document.getElementById('maxTokens').value);
            
            return {
                mode: 'simple',
                prompt,
                model,
                temperature,
                max_tokens: maxTokens,
                count
            };
        } else if (isJsonMode) {
            // JSON模式：使用完整的JSON请求
            const requestJson = document.getElementById('requestJson').value;
            
            try {
                const parsedJson = JSON.parse(requestJson);
                return {
                    mode: 'json',
                    request_json: parsedJson,
                    count
                };
            } catch (error) {
                throw new Error('JSON格式错误: ' + error.message);
            }
        }
    }

    async pollResults() {
        if (!this.currentSessionId) return;
        
        try {
            const response = await fetch(`/results/${this.currentSessionId}`);
            const data = await response.json();
            
            this.updateProgress(data);
            this.updateStats(data);
            this.updateResults(data);
            
            // 如果测试还在进行中，继续轮询
            if (data.status === 'running') {
                setTimeout(() => this.pollResults(), 1000);
            } else {
                // 测试完成，刷新会话列表
                this.loadSessions();
            }
            
        } catch (error) {
            console.error('获取结果失败:', error);
            setTimeout(() => this.pollResults(), 2000); // 出错时延长轮询间隔
        }
    }

    updateProgress(data) {
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (data.status === 'running') {
            progressContainer.style.display = 'block';
            const progress = (data.completed / data.total) * 100;
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `已完成 ${data.completed}/${data.total} 个请求`;
        } else {
            progressContainer.style.display = 'none';
        }
    }

    updateStats(data) {
        const statsContainer = document.getElementById('statsContainer');
        const toolStatsContainer = document.getElementById('toolStatsContainer');
        const toolStatsText = document.getElementById('toolStatsText');
        
        if (data.results && data.results.length > 0) {
            statsContainer.style.display = 'block';
            
            const total = data.results.length;
            const success = data.results.filter(r => r.success === true).length;
            const error = total - success;
            const avgDuration = data.results.reduce((sum, r) => sum + (r.duration || 0), 0) / total;
            
            document.getElementById('totalCount').textContent = total;
            document.getElementById('successCount').textContent = success;
            document.getElementById('errorCount').textContent = error;
            document.getElementById('avgDuration').textContent = `${avgDuration.toFixed(2)}s`;
            
            // 更新工具调用统计
            if (data.tool_call_count !== undefined && data.tool_call_probability !== undefined) {
                toolStatsContainer.style.display = 'block';
                const toolCallCount = data.tool_call_count || 0;
                const totalToolCalls = data.total_tool_calls || 0;
                const probability = data.tool_call_probability || 0;
                
                let statsMessage = `总共 <strong>${total}</strong> 次测试中，有 <strong>${toolCallCount}</strong> 次调用了工具，调用工具概率为 <strong>${probability}%</strong>`;
                
                if (totalToolCalls > toolCallCount) {
                    statsMessage += `（共调用 <strong>${totalToolCalls}</strong> 次工具）`;
                }
                
                toolStatsText.innerHTML = statsMessage;
            } else {
                toolStatsContainer.style.display = 'none';
            }
        } else {
            statsContainer.style.display = 'none';
            toolStatsContainer.style.display = 'none';
        }
    }

    updateResults(data) {
        const container = document.getElementById('resultsContainer');
        
        if (!data.results || data.results.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted p-5">
                    <i class="bi bi-inbox display-4"></i>
                    <p class="mt-3">暂无测试结果</p>
                    <p class="small">请在左侧填写请求内容并开始测试</p>
                </div>
            `;
            return;
        }
        
        const resultsHtml = data.results.map((result, index) => {
            const statusClass = result.success ? 'success' : 'danger';
            const statusIcon = result.success ? 'check-circle' : 'x-circle';
            
            let contentHtml = '';
            if (result.success) {
                // 优先使用新的数据结构
                let contentText = result.content || '';
                let toolCallsData = result.tool_calls || null;
                
                // 如果新数据结构不存在，回退到解析响应摘要
                if (!contentText && !toolCallsData) {
                    const response = result.response || '无响应内容';
                    
                    if (response.includes(' | ')) {
                        const parts = response.split(' | ');
                        for (const part of parts) {
                            if (part.startsWith('内容: ')) {
                                contentText = part.substring(4);
                            } else if (part.startsWith('调用工具: ')) {
                                // 简单解析工具名称
                                const toolNames = part.substring(5).split(', ');
                                toolCallsData = toolNames.map(name => ({ name: name.trim() }));
                            }
                        }
                    } else if (response.startsWith('内容: ')) {
                        contentText = response.substring(4);
                    } else if (response.startsWith('调用工具: ')) {
                        const toolNames = response.substring(5).split(', ');
                        toolCallsData = toolNames.map(name => ({ name: name.trim() }));
                    } else {
                        contentText = response;
                    }
                }
                
                // 显示响应内容
                if (contentText && contentText.trim() && contentText !== '无响应内容') {
                    contentHtml += `
                        <div class="mt-2">
                            <div class="d-flex align-items-center mb-2">
                                <i class="bi bi-chat-text text-primary me-2"></i>
                                <strong class="text-primary">响应内容 (Content):</strong>
                            </div>
                            <div class="border-start border-primary border-3 ps-3">
                                <div class="bg-white p-3 rounded border">
                                    <pre class="mb-0 small text-dark">${this.escapeHtml(contentText.trim())}</pre>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                // 显示工具调用信息
                if (toolCallsData && Array.isArray(toolCallsData) && toolCallsData.length > 0) {
                    contentHtml += `
                        <div class="mt-3">
                            <div class="d-flex align-items-center mb-2">
                                <i class="bi bi-tools text-warning me-2"></i>
                                <strong class="text-warning">工具调用 (Tool Calls):</strong>
                            </div>
                            <div class="border-start border-warning border-3 ps-3">
                                <div class="bg-warning bg-opacity-10 p-3 rounded">
                    `;
                    
                    toolCallsData.forEach((tool, index) => {
                        contentHtml += `
                            <div class="mb-2 ${index > 0 ? 'mt-2 pt-2 border-top' : ''}">
                                <div class="d-flex align-items-center mb-1">
                                    <span class="badge bg-warning text-dark me-2">
                                        <i class="bi bi-gear-fill me-1"></i>
                                        ${this.escapeHtml(tool.name || '未知工具')}
                                    </span>
                                    ${tool.id ? `<small class="text-muted">ID: ${this.escapeHtml(tool.id)}</small>` : ''}
                                </div>
                        `;
                        
                        if (tool.arguments) {
                            let argsDisplay = '';
                            if (typeof tool.arguments === 'object') {
                                argsDisplay = JSON.stringify(tool.arguments, null, 2);
                            } else {
                                argsDisplay = tool.arguments;
                            }
                            contentHtml += `
                                <div class="mt-1">
                                    <small class="text-muted">参数:</small>
                                    <pre class="bg-light p-2 mt-1 small rounded border">${this.escapeHtml(argsDisplay)}</pre>
                                </div>
                            `;
                        }
                        
                        contentHtml += `</div>`;
                    });
                    
                    contentHtml += `
                                </div>
                            </div>
                        </div>
                    `;
                } else if (typeof toolCallsData === 'string') {
                    // 处理字符串形式的工具调用信息（向后兼容）
                    contentHtml += `
                        <div class="mt-3">
                            <div class="d-flex align-items-center mb-2">
                                <i class="bi bi-tools text-warning me-2"></i>
                                <strong class="text-warning">工具调用 (Tool Calls):</strong>
                            </div>
                            <div class="border-start border-warning border-3 ps-3">
                                <div class="bg-warning bg-opacity-10 p-2 rounded">
                                    <span class="badge bg-warning text-dark me-1">
                                        <i class="bi bi-gear-fill me-1"></i>
                                        ${this.escapeHtml(toolCallsData)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                // 如果既没有content也没有tool_calls，显示原始响应
                if ((!contentText || !contentText.trim()) && !toolCallsData) {
                    const response = result.response || '无响应内容';
                    contentHtml += `
                        <div class="mt-2">
                            <div class="d-flex align-items-center mb-2">
                                <i class="bi bi-info-circle text-muted me-2"></i>
                                <strong class="text-muted">响应信息:</strong>
                            </div>
                            <div class="border-start border-secondary border-3 ps-3">
                                <pre class="bg-light p-2 mt-1 small rounded">${this.escapeHtml(response)}</pre>
                            </div>
                        </div>
                    `;
                }
                
                // 显示token使用情况
                if (result.input_tokens || result.output_tokens || result.total_tokens) {
                    contentHtml += `
                        <div class="mt-3">
                            <div class="d-flex align-items-center mb-2">
                                <i class="bi bi-speedometer2 text-info me-2"></i>
                                <strong class="text-info">Token使用统计:</strong>
                            </div>
                            <div class="d-flex gap-2 flex-wrap">
                                <span class="badge bg-info">
                                    <i class="bi bi-arrow-down me-1"></i>
                                    输入: ${result.input_tokens || 0}
                                </span>
                                <span class="badge bg-info">
                                    <i class="bi bi-arrow-up me-1"></i>
                                    输出: ${result.output_tokens || 0}
                                </span>
                                <span class="badge bg-info">
                                    <i class="bi bi-calculator me-1"></i>
                                    总计: ${result.total_tokens || 0}
                                </span>
                            </div>
                        </div>
                    `;
                }
            } else {
                // 显示错误信息
                contentHtml = `
                    <div class="mt-2">
                        <div class="d-flex align-items-center mb-2">
                            <i class="bi bi-exclamation-triangle text-danger me-2"></i>
                            <strong class="text-danger">错误信息:</strong>
                        </div>
                        <div class="border-start border-danger border-3 ps-3">
                            <pre class="bg-danger bg-opacity-10 text-danger p-3 mt-1 small rounded">${this.escapeHtml(result.error || '未知错误')}</pre>
                        </div>
                    </div>
                `;
            }
            
            return `
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span>
                            <i class="bi bi-${statusIcon} text-${statusClass}"></i>
                            请求 #${result.index || (index + 1)}
                        </span>
                        <small class="text-muted">
                            ${result.duration ? `${result.duration}s` : ''}
                            ${result.timestamp ? new Date(result.timestamp).toLocaleTimeString() : ''}
                        </small>
                    </div>
                    <div class="card-body">
                        ${contentHtml}
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = resultsHtml;
    }

    async loadSessions() {
        try {
            const response = await fetch('/sessions');
            const data = await response.json();
            const sessions = data.sessions || [];
            
            const container = document.getElementById('sessionsList');
            
            if (sessions.length === 0) {
                container.innerHTML = '<p class="text-muted small">暂无历史会话</p>';
                return;
            }
            
            const sessionsHtml = sessions.map(session => {
                const date = new Date(session.timestamp).toLocaleString();
                const statusClass = session.status === 'completed' ? 'success' : 
                                  session.status === 'running' ? 'warning' : 'secondary';
                
                return `
                    <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                        <div>
                            <small class="fw-bold">${session.session_id.substring(0, 8)}</small>
                            <br>
                            <small class="text-muted">${date}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${statusClass}">${session.status}</span>
                            <br>
                            <button class="btn btn-sm btn-outline-primary mt-1" 
                                    onclick="llmTester.loadSession('${session.session_id}')">
                                查看
                            </button>
                            <button class="btn btn-sm btn-outline-danger mt-1" 
                                    onclick="llmTester.deleteSession('${session.session_id}')">
                                删除
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = sessionsHtml;
            
        } catch (error) {
            console.error('加载会话失败:', error);
        }
    }

    async loadSession(sessionId) {
        try {
            this.currentSessionId = sessionId;
            const response = await fetch(`/results/${sessionId}`);
            const data = await response.json();
            
            this.updateStats(data);
            this.updateResults(data);
            
        } catch (error) {
            console.error('加载会话失败:', error);
            this.showError('加载会话失败: ' + error.message);
        }
    }

    async deleteSession(sessionId) {
        if (!confirm('确定要删除这个会话吗？')) return;
        
        try {
            const response = await fetch(`/delete/${sessionId}`, { method: 'DELETE' });
            
            if (response.ok) {
                this.loadSessions();
                
                // 如果删除的是当前会话，清空结果显示
                if (this.currentSessionId === sessionId) {
                    this.currentSessionId = null;
                    document.getElementById('resultsContainer').innerHTML = `
                        <div class="text-center text-muted p-5">
                            <i class="bi bi-inbox display-4"></i>
                            <p class="mt-3">暂无测试结果</p>
                            <p class="small">请在左侧填写请求内容并开始测试</p>
                        </div>
                    `;
                    document.getElementById('statsContainer').style.display = 'none';
                    document.getElementById('toolStatsContainer').style.display = 'none';
                }
            } else {
                throw new Error('删除失败');
            }
            
        } catch (error) {
            console.error('删除会话失败:', error);
            this.showError('删除会话失败: ' + error.message);
        }
    }

    async clearAllSessions() {
        if (!confirm('确定要清空所有历史会话吗？')) return;
        
        try {
            const sessions = await fetch('/sessions').then(r => r.json());
            
            for (const session of sessions) {
                await fetch(`/delete/${session.session_id}`, { method: 'DELETE' });
            }
            
            this.loadSessions();
            this.currentSessionId = null;
            
            // 清空结果显示
            document.getElementById('resultsContainer').innerHTML = `
                <div class="text-center text-muted p-5">
                    <i class="bi bi-inbox display-4"></i>
                    <p class="mt-3">暂无测试结果</p>
                    <p class="small">请在左侧填写请求内容并开始测试</p>
                </div>
            `;
            document.getElementById('statsContainer').style.display = 'none';
            document.getElementById('toolStatsContainer').style.display = 'none';
            
        } catch (error) {
            console.error('清空会话失败:', error);
            this.showError('清空会话失败: ' + error.message);
        }
    }

    showError(message) {
        const container = document.getElementById('resultsContainer');
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                ${message}
            </div>
        `;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 全局变量
let llmTester;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async () => {
    console.log('页面DOM加载完成，开始初始化...');
    try {
        llmTester = await LLMTester.create();
        console.log('LLMTester初始化完成');
    } catch (error) {
        console.error('LLMTester初始化失败:', error);
    }
});