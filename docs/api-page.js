/**
 * Executa um smoke test manual sem interpretar a resposta como HTML.
 */
async function testHealthcheck() {
  const baseInput = document.getElementById('api-base');
  const output = document.getElementById('api-output');
  const button = document.getElementById('test-health');
  const baseUrl = baseInput.value.trim().replace(/\/$/, '');

  output.textContent = 'Consultando…';
  button.disabled = true;
  try {
    const targetUrl = new URL('/api/health', `${baseUrl}/`);
    if (window.location.protocol === 'https:' && targetUrl.protocol === 'http:') {
      output.textContent =
        'O navegador bloqueia HTTP a partir desta página HTTPS. Informe uma origem HTTPS ou abra a documentação pela stack local.';
      return;
    }
    const response = await fetch(targetUrl, {
      headers: { Accept: 'application/json' },
    });
    const body = await response.text();
    output.textContent = `HTTP ${response.status}\n${body}`;
  } catch (error) {
    output.textContent = `Falha: ${error.message}`;
  } finally {
    button.disabled = false;
  }
}

document.getElementById('test-health').addEventListener('click', testHealthcheck);
