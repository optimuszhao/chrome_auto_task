async function requestJson(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) throw new Error(data.detail || '请求失败');
  return data;
}

document.addEventListener('click', async (event) => {
  const runFlow = event.target.closest('[data-run-flow]');
  if (runFlow) {
    const data = await requestJson(`/api/flows/${runFlow.dataset.runFlow}/run`, { method: 'POST' });
    location.href = `/runs/${data.run_id}`;
  }
  const deleteFlow = event.target.closest('[data-delete-flow]');
  if (deleteFlow && confirm('确认删除任务？')) {
    await requestJson(`/api/flows/${deleteFlow.dataset.deleteFlow}`, { method: 'DELETE' });
    location.reload();
  }
  const continueRun = event.target.closest('[data-continue-run]');
  if (continueRun) {
    await requestJson(`/api/runs/${continueRun.dataset.continueRun}/continue`, { method: 'POST' });
    location.reload();
  }
  const cancelRun = event.target.closest('[data-cancel-run]');
  if (cancelRun) {
    await requestJson(`/api/runs/${cancelRun.dataset.cancelRun}/cancel`, { method: 'POST' });
    location.reload();
  }
  const deleteSchedule = event.target.closest('[data-delete-schedule]');
  if (deleteSchedule) {
    await requestJson(`/api/schedules/${deleteSchedule.dataset.deleteSchedule}`, { method: 'DELETE' });
    location.reload();
  }
  const enableSchedule = event.target.closest('[data-enable-schedule]');
  if (enableSchedule) {
    await requestJson(`/api/schedules/${enableSchedule.dataset.enableSchedule}/enable`, { method: 'POST' });
    location.reload();
  }
  const disableSchedule = event.target.closest('[data-disable-schedule]');
  if (disableSchedule) {
    await requestJson(`/api/schedules/${disableSchedule.dataset.disableSchedule}/disable`, { method: 'POST' });
    location.reload();
  }
});

const scheduleForm = document.querySelector('#scheduleForm');
if (scheduleForm) {
  scheduleForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = new FormData(scheduleForm);
    const runAt = form.get('run_at');
    await requestJson('/api/schedules', {
      method: 'POST',
      body: JSON.stringify({
        name: form.get('name'),
        flow_id: Number(form.get('flow_id')),
        schedule_type: form.get('schedule_type'),
        cron_expr: form.get('cron_expr') || null,
        interval_seconds: form.get('interval_seconds') ? Number(form.get('interval_seconds')) : null,
        run_at: runAt ? new Date(runAt).toISOString() : null,
        enabled: form.get('enabled') === 'true'
      })
    });
    location.reload();
  });
}
