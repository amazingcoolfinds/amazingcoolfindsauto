/**
 * Cloudflare Worker - Telegram Bot for Sentinel
 * Connects Telegram to GitHub Actions Sentinel Agent
 */

const TELEGRAM_API = 'https://api.telegram.org';
const GH_API = 'https://api.github.com/repos/amazingcoolfinds/amazingcoolfindsauto';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ 
        status: 'ok',
        service: 'Telegram-Sentinel Bridge'
      }), { headers: { 'Content-Type': 'application/json' } });
    }
    
    if (request.method === 'POST') {
      try {
        const update = await request.json();
        await handleUpdate(update, env);
        return new Response('ok');
      } catch (e) {
        return new Response('error');
      }
    }
    
    return new Response('ok');
  }
};

async function handleUpdate(update, env) {
  const message = update.message;
  if (!message) return;
  
  const chatId = message.chat.id;
  const text = message.text || '';
  let response = '';
  
  if (text === '/start' || text === '/help') {
    response = `🧠 *Sentinel Agent*

Hola! Soy el agente de AmazingCoolFinds.

*Comandos:*
• /status - Estado del pipeline
• /sentinel [pregunta] - Pregúntame lo que sea
• /run - Disparar pipeline

Powered by GitHub Models`;
  }
  else if (text === '/status') {
    response = await getStatus(env);
  }
  else if (text === '/run') {
    response = await triggerPipeline(env);
  }
  else if (text.startsWith('/sentinel ')) {
    const question = text.replace('/sentinel ', '');
    response = await askSentinel(question, chatId, env);
  }
  else if (text.startsWith('/sentinel')) {
    response = 'Usa: /sentinel [tu pregunta]\n\nEjemplo: /sentinel cómo está el pipeline?';
  }
  else {
    response = await askSentinel(text, chatId, env);
  }
  
  await sendReply(chatId, response, env);
}

async function sendReply(chatId, text, env) {
  const token = env.TELEGRAM_BOT_TOKEN;
  if (!token) return;
  
  const msg = (text || '').replace(/[*_`#]/g, '');
  
  try {
    await fetch(`${TELEGRAM_API}/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text: msg.substring(0, 4000) })
    });
  } catch (e) {
    console.error('Send error:', e);
  }
}

async function ghFetch(env, path, options = {}) {
  const resp = await fetch(`${GH_API}${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'telegram-sentinel-worker/1.0',
      ...(options.headers || {})
    }
  });
  return resp;
}

async function getStatus(env) {
  try {
    const resp = await ghFetch(env, '/actions/runs?per_page=1');
    
    if (!resp.ok) {
      return `⚠️ GitHub error ${resp.status}`;
    }
    
    const data = await resp.json();
    const run = data.workflow_runs?.[0];
    
    if (!run) {
      return '📭 No hay runs recientes.';
    }
    
    const status = run.conclusion === 'success' ? '✅' : 
                   run.conclusion === 'failure' ? '❌' : '⏳';
    const date = new Date(run.created_at).toLocaleString();
    
    return `${status} ${run.conclusion || 'en progreso'}
📊 Run #${run.run_number}
🕒 ${date}
🔗 Ver: ${run.html_url}`;
    
  } catch (e) {
    return `⚠️ Error: ${e.message}`;
  }
}

async function triggerPipeline(env) {
  try {
    const resp = await ghFetch(env, '/actions/workflows/daily_pipeline.yml/dispatches', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ref: 'main' })
    });
    
    if (resp.status === 204 || resp.status === 200) {
      return '🚀 Pipeline activado!\n\nSe ejecutará en 2-3 minutos.';
    }
    
    return `⚠️ Error ${resp.status}`;
    
  } catch (e) {
    return `⚠️ Error: ${e.message}`;
  }
}

async function askSentinel(question, chatId, env) {
  try {
    const resp = await ghFetch(env, '/actions/workflows/agent_sentinel.yml/dispatches', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ref: 'main',
        inputs: {
          mode: 'think',
          question: question,
          chat_id: chatId.toString()
        }
      })
    });
    
    if (resp.status === 204 || resp.status === 200) {
      return '🧠 Pregunta enviada a Sentinel...\n\nSentinel la procesará con GitHub Models y te responderá aquí en ~1-2 minutos.';
    }
    
    return `⚠️ No pude conectar con Sentinel. Código: ${resp.status}`;
    
  } catch (e) {
    return `⚠️ Error: ${e.message}`;
  }
}
