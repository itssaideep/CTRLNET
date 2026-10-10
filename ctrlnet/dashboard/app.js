// CTRLNET Frontend Application

const terminal = document.getElementById('terminal');
const scanBtn = document.getElementById('scan-btn');
const targetInput = document.getElementById('target-input');
const modelSelect = document.getElementById('model-select');
const modal = document.getElementById('profiler-modal');

// State
let ws = null;
let graphData = { nodes: [], links: [] };
let simulation = null;
let svg, linkGroup, nodeGroup;
let width, height;

// Stats
const stats = { verified: 0, rejected: 0, failed: 0, insufficient: 0 };

function log(msg, type = 'info') {
    const d = new Date();
    const time = `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`;
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `<span class="log-time">[${time}]</span><span class="log-${type}">${msg}</span>`;
    terminal.appendChild(div);
    if(terminal.childElementCount > 200) terminal.removeChild(terminal.firstChild);
    terminal.scrollTop = terminal.scrollHeight;
}

function updateStats() {
    document.getElementById('stat-verified').textContent = stats.verified;
    document.getElementById('stat-rejected').textContent = stats.rejected;
    document.getElementById('stat-failed').textContent = stats.failed;
    document.getElementById('stat-insufficient').textContent = stats.insufficient;
}

// D3.js Network Graph Setup
function initGraph() {
    const container = document.getElementById('graph-container');
    width = container.clientWidth;
    height = container.clientHeight;

    svg = d3.select('#graph-container').append('svg')
        .attr('width', width)
        .attr('height', height);

    // Glow filter
    const defs = svg.append("defs");
    const filter = defs.append("filter").attr("id", "glow");
    filter.append("feGaussianBlur").attr("stdDeviation", "3.5").attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    linkGroup = svg.append('g').attr('class', 'links');
    nodeGroup = svg.append('g').attr('class', 'nodes');

    simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2));
}

function updateGraph() {
    // Links
    const link = linkGroup.selectAll('line').data(graphData.links);
    link.exit().remove();
    const linkEnter = link.enter().append('line')
        .style("stroke", "rgba(0, 212, 255, 0.3)")
        .style("stroke-width", 1);
    const linkMerged = linkEnter.merge(link);

    // Nodes
    const node = nodeGroup.selectAll('circle').data(graphData.nodes, d => d.id);
    node.exit().remove();
    
    const nodeEnter = node.enter().append('circle')
        .attr('r', d => d.type === 'host' ? 12 : 8)
        .style('fill', d => getColorForStatus(d.status))
        .style('stroke', '#fff')
        .style('stroke-width', 1)
        .style('filter', 'url(#glow)')
        .on('click', (event, d) => {
            if (d.type === 'service') showProfiler(d);
        })
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
            
    const nodeMerged = nodeEnter.merge(node);
    
    // Update colors dynamically
    nodeMerged.style('fill', d => getColorForStatus(d.status));

    simulation.nodes(graphData.nodes).on("tick", () => {
        linkMerged
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        nodeMerged
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
    });

    simulation.force("link").links(graphData.links);
    simulation.alpha(1).restart();
}

function getColorForStatus(status) {
    switch(status) {
        case 'VERIFIED': return '#00ff88'; // success
        case 'REJECTED': return '#ff9f1c'; // secondary
        case 'FAILED': return '#ff2d2d';   // critical
        case 'INSUFFICIENT': return '#7dd3fc'; // muted
        case 'analyzing': return '#ff00ff'; // neon pink
        default: return '#00d4ff'; // primary (cyan)
    }
}

// Drag functions
function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x; d.fy = d.y;
}
function dragged(event, d) {
  d.fx = event.x; d.fy = event.y;
}
function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null; d.fy = null;
}

// WebSocket Connection
function connectWS() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onopen = () => log('WebSocket connected to backend', 'success');
    ws.onclose = () => {
        log('WebSocket disconnected. Reconnecting in 3s...', 'error');
        setTimeout(connectWS, 3000);
    };
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleEvent(msg.event, msg.data);
    };
}

// Handle Backend Events
function handleEvent(eventName, data) {
    if (eventName === 'scan_started') {
        log(`Initiating scan on ${data.target}`, 'info');
        graphData.nodes = [{ id: data.target, type: 'gateway', status: 'active' }];
        graphData.links = [];
        updateGraph();
    }
    
    else if (eventName === 'host_discovered') {
        log(`Host discovered: ${data.host} [${data.state}]`, 'info');
        if (!graphData.nodes.find(n => n.id === data.host)) {
            graphData.nodes.push({ id: data.host, type: 'host', status: 'active' });
            // Assume the first node is the gateway/target
            graphData.links.push({ source: graphData.nodes[0].id, target: data.host });
            updateGraph();
        }
    }
    
    else if (eventName === 'service_found') {
        log(`Service detected: ${data.host}:${data.port} (${data.service})`, 'info');
        const svcId = `${data.host}:${data.port}`;
        graphData.nodes.push({ 
            id: svcId, 
            type: 'service', 
            status: 'active',
            host: data.host,
            port: data.port,
            service: data.service,
            data: {} // Holds profiler data
        });
        graphData.links.push({ source: data.host, target: svcId });
        updateGraph();
    }
    
    else if (eventName === 'evidence_extracted') {
        const svcId = `${data.host}:${data.port}`;
        const node = graphData.nodes.find(n => n.id === svcId);
        if(node) node.data.evidence = data.evidence;
    }
    
    else if (eventName === 'llm_analysis_started') {
        log(`LLM analysis started for ${data.host}:${data.port}`, 'warn');
        const svcId = `${data.host}:${data.port}`;
        const node = graphData.nodes.find(n => n.id === svcId);
        if(node) { node.status = 'analyzing'; updateGraph(); }
    }
    
    else if (eventName === 'llm_response') {
        const svcId = `${data.host}:${data.port}`;
        const node = graphData.nodes.find(n => n.id === svcId);
        if(node) node.data.prediction = data.prediction;
    }
    
    else if (eventName === 'service_complete') {
        log(`Analysis complete for ${data.host}:${data.port} -> ${data.status}`, 
            data.status === 'VERIFIED' ? 'success' : (data.status === 'REJECTED' ? 'warn' : 'info'));
            
        const svcId = `${data.host}:${data.port}`;
        const node = graphData.nodes.find(n => n.id === svcId);
        if(node) { 
            node.status = data.status; 
            updateGraph(); 
            
            // Update stats
            if(data.status === 'VERIFIED') stats.verified++;
            else if(data.status === 'REJECTED') stats.rejected++;
            else if(data.status === 'INSUFFICIENT') stats.insufficient++;
            else stats.failed++;
            updateStats();
        }
    }
}

function showProfiler(nodeData) {
    document.getElementById('p-ip').textContent = nodeData.host;
    document.getElementById('p-service').textContent = nodeData.service;
    document.getElementById('p-port').textContent = nodeData.port;
    
    const ev = nodeData.data.evidence || {};
    document.getElementById('p-evidence').textContent = ev.raw_banner || 'No banner extracted';
    
    const pred = nodeData.data.prediction || {};
    document.getElementById('p-product').textContent = pred.product || '---';
    document.getElementById('p-version').textContent = pred.version || '---';
    document.getElementById('p-cpe').textContent = pred.cpe || '---';
    document.getElementById('p-confidence').textContent = pred.confidence ? `${(pred.confidence*100).toFixed(1)}%` : '---';
    
    const statusEl = document.getElementById('p-status');
    statusEl.textContent = nodeData.status;
    statusEl.className = 'badge ' + (nodeData.status || '').toLowerCase();
    
    modal.style.display = 'flex';
}

scanBtn.addEventListener('click', () => {
    const target = targetInput.value;
    const model = modelSelect.value;
    
    fetch(`/api/scan?target=${encodeURIComponent(target)}&model=${encodeURIComponent(model)}`, {
        method: 'POST'
    }).catch(e => log(`Failed to start scan: ${e}`, 'error'));
});

// Init
initGraph();
connectWS();
