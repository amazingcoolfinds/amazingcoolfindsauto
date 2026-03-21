/**
 * Cloudflare Worker - Telegram Bot for Sentinel
 * Allows you to interact with Sentinel via Telegram
 * 
 * Commands:
 * - /start - Welcome message
 * - /status - Get pipeline status
 * - /report - Get latest daily report
 * - /run - Trigger pipeline manually
 * - /sentinel - Ask Sentinel anything
 * - /health - Check API health
 */

const TELEGRAM_API = 'https://api.telegram.org';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Handle Telegram webhook
    if (url.pathname === '/telegram-webhook' || url.pathname === `/telegram-${env.TELEGRAM_BOT_TOKEN}`) {
      return handleTelegramUpdate(request, env);
    }
    
    // Set webhook endpoint
    if (url.pathname === '/set-webhook') {
      const webhookUrl = `${url.origin}/telegram-${env.TELEGRAM_BOT_TOKEN}`;
      const setResponse = await fetch(`${TELEGRAM_API}/bot${env.TELEGRAM_BOT_TOKEN}/setWebhook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: webhookUrl })
      });
      const result = await setResponse.json();
      return new Response(JSON.stringify(result), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'ok',
        service: 'Telegram-Sentinel Bridge',
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response('Telegram Sentinel Bridge is running', { status: 200 });
  }
};

async function handleTelegramUpdate(request, env) {
  try {
    const update = await request.json();
    const chatId = update.message?.chat?.id;
    const text = update.message?.text || '';
    const userName = update.message?.from?.first_name || 'User';
    
    if (!chatId) {
      return new Response('ok', { status: 200 });
    }
    
    let response = '';
    
    // Parse command
    if (text.startsWith('/start')) {
      response = `👋 Hola ${userName}!

Soy *Sentinel*, el agente de mantenimiento de AmazingCoolFinds.

*Comandos disponibles:*
• /status - Estado del pipeline
• /report - Último reporte diario
• /run - Disparar pipeline manualmente
• /health - Salud de las APIs
• /sentinel [pregunta] - Pregúntame cualquier cosa`;
    }
    else if (text.startsWith('/status')) {
      response = await getPipelineStatus(env);
    }
    else if (text.startsWith('/report')) {
      response = await getLatestReport(env);
    }
    else if (text.startsWith('/health')) {
      response = await checkHealth(env);
    }
    else if (text.startsWith('/run')) {
      response = await triggerPipeline(env);
    }
    else if (text.startsWith('/sentinel ')) {
      const question = text.replace('/sentinel ', '');
      response = await askSentinel(question, env);
    }
    else {
      response = `🤔 No entendí ese comando.

*Usa:*
• /start - Ver comandos
• /status - Estado del pipeline
• /report - Reporte diario
• /health - Salud de APIs`;
    }
    
    // Send response to Telegram
    await sendMessage(env.TELEGRAM_BOT_TOKEN, chatId, response);
    
  } catch (error) {
    console.error('Telegram error:', error);
  }
  
  return new Response('ok', { status: 200 });
}

async function sendMessage(botToken, chatId, text) {
  // Escape markdown
  const escapedText = text
    .replace(/\_/g, '\\_')
    .replace(/\*/g, '\\*')
    .replace(/\[/g, '\\[');
  
  await fetch(`${TELEGRAM_API}/bot${botToken}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: escapedText,
      parse_mode: 'MarkdownV2'
    })
  });
}

async function getPipelineStatus(env) {
  try {
    const GH_API = `https://api.github.com/repos/${env.GITHUB_REPO}`;
    const runsResponse = await fetch(`${GH_API}/actions/runs?per_page=3`, {
      headers: {
        'Authorization': `Bearer ${env.GH_PAT || 'NO_TOKEN'}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    });
    
    if (!runsResponse.ok) {
      const errorText = await runsResponse.text();
      return `❌ Error GitHub: ${runsResponse.status} - ${errorText.substring(0, 100)}`;
    }
    
    const runs = await runsResponse.json();
    const latestRun = runs.workflow_runs?.[0];
    
    if (!latestRun) {
      return '📭 No hay runs recientes';
    }
    
    const status = latestRun.conclusion === 'success' ? '✅' : 
                   latestRun.conclusion === 'failure' ? '❌' : '⏳';
    
    const date = new Date(latestRun.created_at).toLocaleString();
    
    return `*Estado del Pipeline*

${status} Último run: ${latestRun.conclusion || 'en progreso'}
📅 ${date}
🔗 [Ver en GitHub](${latestRun.html_url})`;
    
  } catch (error) {
    return `❌ Error: ${error.message}`;
  }
}

async function getLatestReport(env) {
  try {
    // Read the last report from pipeline_health.json
    const healthUrl = `https://raw.githubusercontent.com/${env.GITHUB_REPO}/main/data/pipeline_health.json`;
    const response = await fetch(healthUrl);
    
    if (!response.ok) {
      return '📭 No hay reportes disponibles aún';
    }
    
    const health = await response.json();
    const lastRun = health.runs?.[health.runs.length - 1];
    
    if (!lastRun) {
      return '📭 No hay datos de runs';
    }
    
    const status = lastRun.conclusion === 'success' ? '✅' : 
                   lastRun.conclusion === 'failure' ? '❌' : '⏳';
    
    return `*Reporte Diario*

📅 ${lastRun.date}
${status} Estado: ${lastRun.conclusion || 'desconocido'}
📦 Productos: ${lastRun.products_processed || 0}
📹 YouTube: ${lastRun.youtube_uploaded || 0}
🔗 [Ver logs](${lastRun.url || 'N/A'})`;
    
  } catch (error) {
    return `❌ Error: ${error.message}`;
  }
}

async function checkHealth(env) {
  try {
    const ghResponse = await fetch('https://api.github.com/rate_limit', {
      headers: { 'Authorization': `Bearer ${env.GH_PAT}` }
    });
    
    if (ghResponse.ok) {
      const ghData = await ghResponse.json();
      const remaining = ghData.rate?.remaining || 0;
      return `*Health Check*

🟢 GitHub API: ${remaining} requests restantes
🟢 Cloudflare: Conectado
🟢 Sentinel: Activo
🔑 GitHub Token: ${env.GH_PAT ? '✅ Configurado' : '❌ Faltando'}`;
    } else {
      return `*Health Check*

🟢 Cloudflare: Conectado
🟢 Sentinel: Activo
🔑 GitHub Token: ${env.GH_PAT ? '✅ Configurado' : '❌ Faltando'}
⚠️ GitHub API error: ${ghResponse.status}`;
    }
    
  } catch (error) {
    return `*Health Check*

🟢 Cloudflare: Conectado
🟢 Sentinel: Activo
🔑 GitHub Token: ${env.GH_PAT ? '✅' : '❌'}
❌ Error: ${error.message}`;
  }
}

async function triggerPipeline(env) {
  try {
    // Use Make.com webhook to trigger pipeline
    const makeUrl = env.MAKE_WEBHOOK_URL;
    if (makeUrl) {
      await fetch(makeUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          source: 'telegram',
          command: 'run-pipeline',
          timestamp: new Date().toISOString()
        })
      });
      return '🚀 *Pipeline disparado!*\n\nSe ejecutará en ~2-3 minutos. Usa /status para ver el progreso.';
    }
    
    // Fallback: GitHub API (if token works)
    if (env.GH_PAT) {
      const GH_API = `https://api.github.com/repos/${env.GITHUB_REPO}`;
      const response = await fetch(`${GH_API}/dispatches`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.GH_PAT}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          event_type: 'telegram-command',
          client_payload: { command: 'run-pipeline' }
        })
      });
      
      if (response.status === 204) {
        return '🚀 *Pipeline disparado!*\n\nEl pipeline se ejecutará en ~2-3 minutos. Usa /status para ver el progreso.';
      }
    }
    
    return '⚠️ No hay forma de disparar el pipeline automáticamente.\n\nPuedes dispararlo manualmente desde GitHub Actions.';
    
  } catch (error) {
    return `❌ Error: ${error.message}`;
  }
}

async function askSentinel(question, env) {
  try {
    // Use Make.com webhook
    const makeUrl = env.MAKE_WEBHOOK_URL;
    if (makeUrl) {
      await fetch(makeUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: 'telegram',
          command: 'sentinel',
          question: question,
          timestamp: new Date().toISOString()
        })
      });
      return `🧠 *Pregunta enviada a Sentinel*\n\nSentinel la procesará y te responderá. Espera ~1-2 minutos.`;
    }
    
    return '⚠️ Función no disponible temporalmente.';
    
  } catch (error) {
    return `❌ Error: ${error.message}`;
  }
}
