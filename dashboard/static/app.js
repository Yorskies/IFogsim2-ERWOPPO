// ==============================================================================
// ERWO-PPO LIVE RESEARCH DASHBOARD SCRIPT
// ==============================================================================

// Configuration & Constants
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";

const NODE_DEFINITIONS = [
    { id: 0, label: 'Node 0\nIoT Broker (100 Devs)', tier: 'Tier 1 (IoT)', group: 'iot', x: 0, y: 160 },
    { id: 1, label: 'Node 1\nFog A', tier: 'Tier 2 (Fog)', group: 'fog', x: -200, y: 0 },
    { id: 2, label: 'Node 2\nFog B', tier: 'Tier 2 (Fog)', group: 'fog', x: -100, y: 0 },
    { id: 3, label: 'Node 3\nFog C', tier: 'Tier 2 (Fog)', group: 'fog', x: 0, y: 0 },
    { id: 4, label: 'Node 4\nFog D', tier: 'Tier 2 (Fog)', group: 'fog', x: 100, y: 0 },
    { id: 5, label: 'Node 5\nFog E', tier: 'Tier 2 (Fog)', group: 'fog', x: 200, y: 0 },
    { id: 6, label: 'Node 6\nCloud DC', tier: 'Tier 3 (Cloud)', group: 'cloud', x: 0, y: -160 },
];

let cumulativeReward = 0.0;
const MAX_CHART_POINTS = 40;

// ==============================================================================
// 1. CHART INITIALIZATION (CHART.JS)
// ==============================================================================
const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    scales: {
        x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { maxTicksLimit: 10, font: { size: 10 } }
        },
        y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { font: { size: 10 } }
        }
    },
    plugins: {
        legend: {
            position: 'top',
            labels: { boxWidth: 12, padding: 10, font: { size: 11 } }
        }
    }
};

// Reward Chart
const rewardCtx = document.getElementById('rewardChart').getContext('2d');
const rewardChart = new Chart(rewardCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Step Reward',
            data: [],
            borderColor: '#22d3ee',
            backgroundColor: 'rgba(34, 211, 238, 0.12)',
            borderWidth: 2,
            fill: true,
            tension: 0.3,
            pointRadius: 2,
        }]
    },
    options: commonChartOptions
});

// Multi-Objective Performance Chart
const perfCtx = document.getElementById('performanceChart').getContext('2d');
const perfChart = new Chart(perfCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Latency Score',
                data: [],
                borderColor: '#c084fc',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 1,
            },
            {
                label: 'Energy Efficiency',
                data: [],
                borderColor: '#34d399',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 1,
            },
            {
                label: 'QoS Satisfaction',
                data: [],
                borderColor: '#fbbf24',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 1,
            }
        ]
    },
    options: commonChartOptions
});

// ==============================================================================
// 2. NETWORK TOPOLOGY INITIALIZATION (VIS.JS)
// ==============================================================================
const visNodes = new vis.DataSet(
    NODE_DEFINITIONS.map(n => ({
        id: n.id,
        label: n.label,
        group: n.group,
        x: n.x,
        y: n.y,
        shape: 'box',
        margin: 10,
        font: { color: '#f8fafc', size: 12, multi: true, bold: true },
        color: {
            background: n.group === 'cloud' ? '#7e57c2' : (n.group === 'fog' ? '#1e293b' : '#0284c7'),
            border: '#334155'
        },
        borderWidth: 2,
    }))
);

const visEdges = new vis.DataSet([
    // Tier 1 to Tier 2 Links (Wireless)
    { id: 'e01', from: 0, to: 1, color: { color: 'rgba(255,255,255,0.2)' }, width: 1.5, dashes: true },
    { id: 'e02', from: 0, to: 2, color: { color: 'rgba(255,255,255,0.2)' }, width: 1.5, dashes: true },
    { id: 'e03', from: 0, to: 3, color: { color: 'rgba(255,255,255,0.2)' }, width: 1.5, dashes: true },
    { id: 'e04', from: 0, to: 4, color: { color: 'rgba(255,255,255,0.2)' }, width: 1.5, dashes: true },
    { id: 'e05', from: 0, to: 5, color: { color: 'rgba(255,255,255,0.2)' }, width: 1.5, dashes: true },
    // Tier 2 to Tier 3 Links (WAN / Backbone)
    { id: 'e16', from: 1, to: 6, color: { color: 'rgba(255,255,255,0.2)' }, width: 2 },
    { id: 'e26', from: 2, to: 6, color: { color: 'rgba(255,255,255,0.2)' }, width: 2 },
    { id: 'e36', from: 3, to: 6, color: { color: 'rgba(255,255,255,0.2)' }, width: 2 },
    { id: 'e46', from: 4, to: 6, color: { color: 'rgba(255,255,255,0.2)' }, width: 2 },
    { id: 'e56', from: 5, to: 6, color: { color: 'rgba(255,255,255,0.2)' }, width: 2 },
    // Direct IoT to Cloud Link
    { id: 'e06', from: 0, to: 6, color: { color: 'rgba(255,255,255,0.1)' }, width: 1, dashes: [4, 4] }
]);

const networkContainer = document.getElementById('network-graph');
const networkData = { nodes: visNodes, edges: visEdges };
const networkOptions = {
    physics: false, // Posisi tier tetap (hierarkis terkunci)
    interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
    }
};
const network = new vis.Network(networkContainer, networkData, networkOptions);

// ==============================================================================
// 3. TABLE INITIALIZATION (NODE RESOURCE MONITOR)
// ==============================================================================
const tbody = document.getElementById('node-tbody');
function initNodeTable() {
    tbody.innerHTML = '';
    NODE_DEFINITIONS.forEach(node => {
        const tr = document.createElement('tr');
        tr.id = `node-row-${node.id}`;
        tr.className = 'node-row';
        tr.innerHTML = `
            <td><strong>${node.label.replace('\n', ' - ')}</strong></td>
            <td><span class="legend-dot ${node.group}-dot"></span> ${node.tier.split(' ')[0]}</td>
            <td>
                <div class="bar-container">
                    <div class="progress-track">
                        <div id="cpu-bar-${node.id}" class="progress-fill" style="width: 0%; background: #3b82f6;"></div>
                    </div>
                    <span id="cpu-val-${node.id}" class="bar-val">0%</span>
                </div>
            </td>
            <td>
                <div class="bar-container">
                    <div class="progress-track">
                        <div id="queue-bar-${node.id}" class="progress-fill" style="width: 0%; background: #8b5cf6;"></div>
                    </div>
                    <span id="queue-val-${node.id}" class="bar-val">0%</span>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
initNodeTable();

// ==============================================================================
// 3B. 100 IOT DEVICES FLEET GRID INITIALIZATION
// ==============================================================================
const fleetGrid = document.getElementById('fleet-grid');
function initFleetGrid() {
    if (!fleetGrid) return;
    fleetGrid.innerHTML = '';
    for (let i = 0; i < 100; i++) {
        const cell = document.createElement('div');
        cell.id = `dev-cell-${i}`;
        cell.className = 'dev-cell';
        cell.textContent = i;
        cell.title = `Device #${i} | Battery: 100%`;
        cell.style.backgroundColor = '#10b981';
        fleetGrid.appendChild(cell);
    }
}
initFleetGrid();

function updateFleetGrid(batteries, activeSrcId, meanBatt, depletedCount) {
    if (!batteries || batteries.length === 0) return;

    for (let i = 0; i < batteries.length && i < 100; i++) {
        const cell = document.getElementById(`dev-cell-${i}`);
        if (!cell) continue;

        const b = batteries[i];
        let color = '#10b981'; // Green >= 60%
        if (b < 0.10) {
            color = '#7f1d1d'; // Critical Dark Red
        } else if (b < 0.25) {
            color = '#ef4444'; // Red < 25%
        } else if (b < 0.60) {
            color = '#f59e0b'; // Amber < 60%
        }

        cell.style.backgroundColor = color;
        cell.title = `Device #${i} | Battery: ${(b * 100).toFixed(0)}%`;

        if (i === activeSrcId) {
            cell.classList.add('active-src');
        } else {
            cell.classList.remove('active-src');
        }
    }

    if (activeSrcId !== undefined) {
        const badge = document.getElementById('fleet-active-src');
        if (badge) badge.textContent = `Device #${activeSrcId}`;
    }

    if (meanBatt !== undefined) {
        const battElem = document.getElementById('fleet-mean-batt');
        if (battElem) battElem.textContent = `${(meanBatt * 100).toFixed(1)}%`;
    }

    if (depletedCount !== undefined) {
        const depElem = document.getElementById('fleet-depleted-count');
        if (depElem) {
            depElem.textContent = `${depletedCount} Units`;
            if (depletedCount > 0) {
                depElem.className = 'badge badge-violated';
            } else {
                depElem.className = 'badge badge-success';
            }
        }
    }
}

// ==============================================================================
// 4. UI UPDATE HELPERS
// ==============================================================================
function getLoadColor(val) {
    if (val > 0.75) return '#f87171'; // Red
    if (val > 0.45) return '#fbbf24'; // Amber
    return '#34d399';                // Emerald
}

function updateTopology(nodeCpuLoads, action) {
    NODE_DEFINITIONS.forEach(n => {
        const load = (nodeCpuLoads && nodeCpuLoads[n.id] !== undefined) ? nodeCpuLoads[n.id] : 0.0;
        const colorHex = getLoadColor(load);

        const isChosen = (n.id === action);
        visNodes.update({
            id: n.id,
            color: {
                background: isChosen ? '#0f172a' : (n.group === 'cloud' ? '#4c1d95' : '#1e293b'),
                border: isChosen ? '#22d3ee' : colorHex,
                highlight: { border: '#22d3ee' }
            },
            borderWidth: isChosen ? 4 : 2,
            shadow: isChosen ? { enabled: true, color: '#22d3ee', size: 15 } : false
        });
    });

    // Highlight transmission edge
    visEdges.getIds().forEach(edgeId => {
        const edge = visEdges.get(edgeId);
        if (action === 0) {
            visEdges.update({ id: edgeId, color: { color: 'rgba(255,255,255,0.15)' }, width: 1.5 });
        } else if (action === 6 && edgeId === 'e06') {
            visEdges.update({ id: edgeId, color: { color: '#f59e0b' }, width: 3.5 });
        } else if (edgeId === `e0${action}`) {
            visEdges.update({ id: edgeId, color: { color: '#22d3ee' }, width: 3.5 });
        } else {
            visEdges.update({ id: edgeId, color: { color: 'rgba(255,255,255,0.15)' }, width: 1.5 });
        }
    });
}

function updateNodeTable(cpuLoads, queues, action) {
    NODE_DEFINITIONS.forEach(n => {
        const tr = document.getElementById(`node-row-${n.id}`);
        if (!tr) return;

        if (n.id === action) {
            tr.classList.add('active-row');
        } else {
            tr.classList.remove('active-row');
        }

        const cpu = (cpuLoads && cpuLoads[n.id] !== undefined) ? cpuLoads[n.id] : 0.0;
        const cpuPct = Math.round(cpu * 100);
        const cpuBar = document.getElementById(`cpu-bar-${n.id}`);
        const cpuVal = document.getElementById(`cpu-val-${n.id}`);
        if (cpuBar) {
            cpuBar.style.width = `${cpuPct}%`;
            cpuBar.style.backgroundColor = getLoadColor(cpu);
        }
        if (cpuVal) cpuVal.textContent = `${cpuPct}%`;

        const q = (queues && queues[n.id] !== undefined) ? queues[n.id] : 0.0;
        const qPct = Math.round(q * 100);
        const qBar = document.getElementById(`queue-bar-${n.id}`);
        const qVal = document.getElementById(`queue-val-${n.id}`);
        if (qBar) {
            qBar.style.width = `${qPct}%`;
        }
        if (qVal) qVal.textContent = `${qPct}%`;
    });
}

function updateCharts(step, reward, latency, energy, qos) {
    if (rewardChart.data.labels.length > MAX_CHART_POINTS) {
        rewardChart.data.labels.shift();
        rewardChart.data.datasets[0].data.shift();

        perfChart.data.labels.shift();
        perfChart.data.datasets[0].data.shift();
        perfChart.data.datasets[1].data.shift();
        perfChart.data.datasets[2].data.shift();
    }

    rewardChart.data.labels.push(`S${step}`);
    rewardChart.data.datasets[0].data.push(reward);
    rewardChart.update();

    perfChart.data.labels.push(`S${step}`);
    perfChart.data.datasets[0].data.push(latency);
    perfChart.data.datasets[1].data.push(energy);
    perfChart.data.datasets[2].data.push(qos);
    perfChart.update();
}

function resetUI() {
    cumulativeReward = 0.0;
    rewardChart.data.labels = [];
    rewardChart.data.datasets[0].data = [];
    rewardChart.update();

    perfChart.data.labels = [];
    perfChart.data.datasets.forEach(d => d.data = []);
    perfChart.update();

    document.getElementById('stat-step').textContent = 'Step 0';
    document.getElementById('stat-episode').textContent = 'Episode 1';
    document.getElementById('stat-action').textContent = '-';
    document.getElementById('stat-tier').textContent = 'Idle';
    document.getElementById('stat-load').textContent = '0.0000';
    document.getElementById('stat-reward').textContent = '0.00';
    document.getElementById('stat-cum-reward').textContent = 'Cumulative: 0.00';
    document.getElementById('stat-qos').textContent = '0.00';

    const slaElem = document.getElementById('stat-sla');
    slaElem.innerHTML = `<span class="badge badge-success">COMPLIANT</span>`;
    document.getElementById('stat-sla-sub').textContent = 'Ready';

    initNodeTable();
    initFleetGrid();
    updateTopology([0,0,0,0,0,0,0], -1);
}

// ==============================================================================
// 5. WEBSOCKET & BACKEND COMMUNICATION
// ==============================================================================
let socket = null;

function sendControl(cmd, value = null) {
    fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd, value: value })
    }).catch(err => console.error('Error control command:', err));
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    socket = new WebSocket(wsUrl);

    const dot = document.getElementById('conn-dot');
    const statusText = document.getElementById('conn-status');

    socket.onopen = () => {
        dot.classList.add('connected');
        statusText.textContent = 'Live Connected';
    };

    socket.onclose = () => {
        dot.classList.remove('connected');
        statusText.textContent = 'Disconnected (Reconnecting...)';
        setTimeout(connectWebSocket, 2000);
    };

    socket.onerror = (err) => {
        console.warn('WebSocket error:', err);
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'init') {
                if (data.status) {
                    document.getElementById('select-method').value = data.status.method || 'ERWO-PPO';
                    document.getElementById('select-workload').value = data.status.workload || 'dynamic';
                    document.getElementById('slider-speed').value = data.status.speed_ms || 150;
                    document.getElementById('speed-display').textContent = `${data.status.speed_ms || 150} ms`;
                    document.getElementById('live-method-badge').textContent = data.status.method || 'ERWO-PPO';
                }
                return;
            }

            if (data.type === 'reset') {
                resetUI();
                return;
            }

            // Normal Simulation Data
            const step = data.step || 0;
            const action = data.action !== undefined ? data.action : 0;
            const episode = data.episode || 1;
            const reward = data.reward || 0.0;
            cumulativeReward += reward;

            // Update Progress & Action Stats
            document.getElementById('stat-step').textContent = `Step ${step}`;
            document.getElementById('stat-episode').textContent = `Episode ${episode}`;

            const nodeDef = NODE_DEFINITIONS[action] || { label: `Node ${action}`, tier: 'Unknown' };
            document.getElementById('stat-action').textContent = nodeDef.label.replace('\n', ' ');
            document.getElementById('stat-tier').textContent = nodeDef.tier;

            // SLA Status
            const isViolated = Boolean(data.is_violated);
            const slaElem = document.getElementById('stat-sla');
            const slaSub = document.getElementById('stat-sla-sub');
            if (isViolated) {
                slaElem.innerHTML = `<span class="badge badge-violated">⚠ VIOLATED</span>`;
                slaSub.textContent = 'Latency exceeded deadline!';
            } else {
                slaElem.innerHTML = `<span class="badge badge-success">✔ COMPLIANT</span>`;
                slaSub.textContent = 'Processed on-time (SLA Met)';
            }

            // Load Imbalance
            const loadImb = data.load_imbalance !== undefined ? data.load_imbalance : 0.0;
            document.getElementById('stat-load').textContent = loadImb.toFixed(4);

            // Reward
            document.getElementById('stat-reward').textContent = reward.toFixed(2);
            document.getElementById('stat-cum-reward').textContent = `Cumulative: ${cumulativeReward.toFixed(2)}`;

            // QoS
            const qos = data.qos_satisfaction || 0.0;
            document.getElementById('stat-qos').textContent = qos.toFixed(2);

            // Task Profile
            if (data.task_data_size !== undefined) {
                document.getElementById('task-size').textContent = `${(data.task_data_size * 100).toFixed(1)} KB`;
            }
            if (data.task_mi !== undefined) {
                document.getElementById('task-mi').textContent = `${(data.task_mi * 1000).toFixed(0)} MI`;
            }
            if (data.task_deadline !== undefined) {
                document.getElementById('task-deadline').textContent = `${(data.task_deadline * 2.5).toFixed(2)} s`;
            }
            if (data.task_priority !== undefined) {
                const p = data.task_priority;
                document.getElementById('task-priority').textContent = p > 0.6 ? 'High (Q1)' : (p > 0.3 ? 'Medium' : 'Low');
            }

            // Method Badge
            if (data.method_name) {
                document.getElementById('live-method-badge').textContent = data.method_name;
            }

            // Charts
            updateCharts(step, reward, data.latency || 0, data.energy || 0, qos);

            // Topology & Table
            updateTopology(data.node_cpu || [], action);
            updateNodeTable(data.node_cpu || [], data.node_queues || [], action);

            // 100 Edge Devices Fleet Update
            if (data.devices_battery && data.devices_battery.length > 0) {
                updateFleetGrid(
                    data.devices_battery,
                    data.source_device_id,
                    data.mean_fleet_battery,
                    data.depleted_devices_count
                );
            }

        } catch (err) {
            console.error('Error handling WebSocket message:', err);
        }
    };
}

// ==============================================================================
// 6. EVENT LISTENERS & TOOLBAR CONTROLS
// ==============================================================================
document.getElementById('btn-play').addEventListener('click', () => {
    sendControl('play');
});

document.getElementById('btn-pause').addEventListener('click', () => {
    sendControl('pause');
});

document.getElementById('btn-reset').addEventListener('click', () => {
    sendControl('reset');
});

document.getElementById('select-method').addEventListener('change', (e) => {
    sendControl('set_method', e.target.value);
    document.getElementById('live-method-badge').textContent = e.target.value;
});

document.getElementById('select-workload').addEventListener('change', (e) => {
    sendControl('set_workload', e.target.value);
});

const speedSlider = document.getElementById('slider-speed');
const speedDisplay = document.getElementById('speed-display');
speedSlider.addEventListener('input', (e) => {
    const val = e.target.value;
    speedDisplay.textContent = `${val} ms`;
    sendControl('set_speed', parseInt(val));
});

// Start WebSocket connection
connectWebSocket();
