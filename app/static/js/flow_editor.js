const actionFields = {
  goto: ['url', 'timeout'],
  click: ['selector', 'timeout'],
  fill: ['selector', 'value', 'timeout'],
  wait: ['selector', 'timeout'],
  sleep: ['seconds'],
  screenshot: ['path'],
  assert_text: ['text', 'timeout'],
  assert_visible: ['selector', 'timeout'],
  select: ['selector', 'value'],
  upload: ['selector', 'file_path'],
  download: ['selector', 'save_as'],
  manual_confirm: ['message']
};
const actionLabels = {
  goto: '打开页面 / goto',
  click: '点击元素 / click',
  fill: '填写输入框 / fill',
  wait: '等待元素 / wait',
  sleep: '固定等待 / sleep',
  screenshot: '截图 / screenshot',
  assert_text: '校验文字 / assert_text',
  assert_visible: '校验可见 / assert_visible',
  select: '选择下拉框 / select',
  upload: '上传文件 / upload',
  download: '下载文件 / download',
  manual_confirm: '人工确认 / manual_confirm'
};
let steps = [];
let current = 0;

const els = {
  flowId: document.querySelector('#flowId'),
  flowName: document.querySelector('#flowName'),
  flowDescription: document.querySelector('#flowDescription'),
  flowEnabled: document.querySelector('#flowEnabled'),
  storageState: document.querySelector('#storageState'),
  list: document.querySelector('#stepList'),
  action: document.querySelector('#stepAction'),
  selector: document.querySelector('#stepSelector'),
  value: document.querySelector('#stepValue'),
  url: document.querySelector('#stepUrl'),
  timeout: document.querySelector('#stepTimeout'),
  path: document.querySelector('#stepPath'),
  message: document.querySelector('#stepMessage'),
  text: document.querySelector('#stepText'),
  seconds: document.querySelector('#stepSeconds'),
  file_path: document.querySelector('#stepFilePath'),
  save_as: document.querySelector('#stepSaveAs'),
  description: document.querySelector('#stepDescription'),
  yaml: document.querySelector('#yamlContent'),
  msg: document.querySelector('#editorMessage')
};

Object.keys(actionFields).forEach(action => {
  const option = document.createElement('option');
  option.value = action;
  option.textContent = actionLabels[action] || action;
  els.action.appendChild(option);
});

const defaultFlow = () => ({
  name: 'Mock 登录并提交表单',
  description: '用于验证浏览器自动化平台的测试流程',
  browser: { headless: true, slow_mo: 100, storage_state: '' },
  variables: { username: 'admin', password: '123456', title: '自动化测试标题' },
  steps: [
    { action: 'goto', url: 'http://127.0.0.1:8000/mock-site' },
    { action: 'fill', selector: '#username', value: '${username}' },
    { action: 'fill', selector: '#password', value: '${password}' },
    { action: 'click', selector: '#loginBtn' },
    { action: 'wait', selector: '#dashboard' },
    { action: 'click', selector: '#openFormBtn' },
    { action: 'fill', selector: '#title', value: '${title}' },
    { action: 'select', selector: '#level', value: 'high' },
    { action: 'screenshot', path: 'logs/mock-before-submit.png' },
    { action: 'click', selector: '#submitBtn' },
    { action: 'assert_text', text: '提交成功' }
  ]
});

function stepFromFields() {
  const step = { action: els.action.value };
  for (const key of ['selector', 'value', 'url', 'path', 'message', 'text', 'file_path', 'save_as', 'description']) {
    if (els[key].value) step[key] = els[key].value;
  }
  if (els.timeout.value) step.timeout = Number(els.timeout.value);
  if (els.seconds.value) step.seconds = Number(els.seconds.value);
  return step;
}

function fieldsFromStep(step) {
  for (const key of ['selector', 'value', 'url', 'timeout', 'path', 'message', 'text', 'seconds', 'file_path', 'save_as', 'description']) {
    els[key].value = step[key] ?? '';
  }
  els.action.value = step.action || 'goto';
}

function persistCurrent() {
  if (steps[current]) steps[current] = stepFromFields();
}

function renderSteps() {
  els.list.innerHTML = '';
  steps.forEach((step, index) => {
    const li = document.createElement('li');
    li.className = index === current ? 'active' : '';
    li.textContent = `${index + 1}. ${actionLabels[step.action] || step.action}`;
    li.addEventListener('click', () => {
      persistCurrent();
      current = index;
      fieldsFromStep(steps[current]);
      renderSteps();
    });
    els.list.appendChild(li);
  });
}

function formToYaml() {
  persistCurrent();
  const data = {
    name: els.flowName.value || '未命名任务',
    description: els.flowDescription.value || '',
    browser: { headless: true, slow_mo: 100, storage_state: els.storageState.value || '' },
    variables: {},
    steps
  };
  els.yaml.value = jsyaml.dump(data, { lineWidth: -1, noRefs: true });
}

function yamlToForm() {
  const data = jsyaml.load(els.yaml.value || '');
  els.flowName.value = data.name || '';
  els.flowDescription.value = data.description || '';
  els.storageState.value = data.browser?.storage_state || '';
  steps = Array.isArray(data.steps) ? data.steps : [];
  current = 0;
  fieldsFromStep(steps[0] || { action: 'goto' });
  renderSteps();
}

async function saveFlow() {
  formToYaml();
  const flowId = els.flowId.value;
  const payload = {
    name: els.flowName.value,
    description: els.flowDescription.value,
    yaml_content: els.yaml.value,
    enabled: els.flowEnabled.value === 'true'
  };
  const url = flowId ? `/api/flows/${flowId}` : '/api/flows';
  const method = flowId ? 'PUT' : 'POST';
  const data = await requestJson(url, { method, body: JSON.stringify(payload) });
  location.href = `/flows/${data.id}/edit`;
}

async function validateYaml() {
  const flowId = els.flowId.value || 0;
  await requestJson(`/api/flows/${flowId}/validate`, { method: 'POST', body: JSON.stringify({ yaml_content: els.yaml.value }) });
  els.msg.textContent = '校验通过';
}

async function formatYaml() {
  const flowId = els.flowId.value || 0;
  const data = await requestJson(`/api/flows/${flowId}/format`, { method: 'POST', body: JSON.stringify({ yaml_content: els.yaml.value }) });
  els.yaml.value = data.yaml_content;
  yamlToForm();
}

document.querySelector('#addStepBtn').addEventListener('click', () => {
  persistCurrent();
  steps.push({ action: 'click', selector: '' });
  current = steps.length - 1;
  fieldsFromStep(steps[current]);
  renderSteps();
});
document.querySelector('#deleteStepBtn').addEventListener('click', () => {
  steps.splice(current, 1);
  current = Math.max(0, current - 1);
  fieldsFromStep(steps[current] || { action: 'goto' });
  renderSteps();
});
document.querySelector('#moveUpBtn').addEventListener('click', () => {
  persistCurrent();
  if (current > 0) [steps[current - 1], steps[current]] = [steps[current], steps[current - 1]], current--;
  renderSteps();
});
document.querySelector('#moveDownBtn').addEventListener('click', () => {
  persistCurrent();
  if (current < steps.length - 1) [steps[current + 1], steps[current]] = [steps[current], steps[current + 1]], current++;
  renderSteps();
});
document.querySelector('#formToYamlBtn').addEventListener('click', formToYaml);
document.querySelector('#yamlToFormBtn').addEventListener('click', yamlToForm);
document.querySelector('#saveFlowBtn').addEventListener('click', () => saveFlow().catch(err => els.msg.textContent = err.message));
document.querySelector('#validateYamlBtn').addEventListener('click', () => validateYaml().catch(err => els.msg.textContent = err.message));
document.querySelector('#formatYamlBtn').addEventListener('click', () => formatYaml().catch(err => els.msg.textContent = err.message));
document.querySelector('#runFlowBtn').addEventListener('click', async () => {
  const data = await requestJson(`/api/flows/${els.flowId.value}/run`, { method: 'POST' });
  location.href = `/runs/${data.run_id}`;
});

if (!els.yaml.value.trim()) els.yaml.value = jsyaml.dump(defaultFlow(), { lineWidth: -1, noRefs: true });
yamlToForm();
