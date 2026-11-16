import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isValidDate, isValidWeekId, weekMonday, weekSunday, targetWeek, fiscalYear,
  groupByFiscalYear, tagSlug, countRecent, todayInTokyo } from './week-logic.ts';

test('isValidDate / isValidWeekId', () => {
  assert.equal(isValidDate('2024-02-29'), true);
  assert.equal(isValidDate('2026-02-30'), false);
  assert.equal(isValidDate('2026-11-5'), false);
  assert.equal(isValidWeekId('2026-11-09'), true);   // 月曜
  assert.equal(isValidWeekId('2026-11-15'), false);  // 日曜
  assert.equal(isValidWeekId('memo'), false);
});

test('weekMonday / weekSunday', () => {
  assert.equal(weekMonday('2026-11-15'), '2026-11-09');  // 日曜
  assert.equal(weekMonday('2026-11-16'), '2026-11-16');  // 月曜
  assert.equal(weekMonday('2027-01-01'), '2026-12-28');  // 年またぎ
  assert.equal(weekSunday('2026-11-09'), '2026-11-15');
});

test('targetWeek: 既定は直前に終わった週', () => {
  assert.deepEqual(targetWeek(undefined, '2026-11-16'), { monday: '2026-11-09', sunday: '2026-11-15' });
  assert.deepEqual(targetWeek(undefined, '2026-11-15'), { monday: '2026-11-02', sunday: '2026-11-08' });
  assert.deepEqual(targetWeek('2026-11-12', '2026-11-16'), { monday: '2026-11-09', sunday: '2026-11-15' });
  assert.throws(() => targetWeek('2026-02-30', '2026-11-16'), /Invalid date/);
});

test('fiscalYear: 4月始まり・月曜で判定', () => {
  assert.equal(fiscalYear('2026-03-30'), 2025);
  assert.equal(fiscalYear('2026-04-06'), 2026);
});

test('groupByFiscalYear', () => {
  assert.deepEqual(groupByFiscalYear([{ id: '2026-03-30' }, { id: '2026-11-09' }, { id: '2026-04-06' }]), [
    [2026, [{ id: '2026-11-09' }, { id: '2026-04-06' }]],
    [2025, [{ id: '2026-03-30' }]],
  ]);
});

test('tagSlug', () => {
  assert.equal(new Set(['C#', 'C++', 'C', 'CI/CD'].map(tagSlug)).size, 4);
  assert.equal(tagSlug('AWS'), tagSlug('aws'));
  assert.equal(tagSlug('猫見守り'), '猫見守り');
  assert.doesNotMatch(tagSlug('CI/CD'), /\//);
});

test('countRecent: 今週含む4週', () => {
  const r = countRecent([
    { id: '2026-11-16', tags: ['AWS', 'MCP'] },  // 今週
    { id: '2026-10-26', tags: ['aws'] },         // 3週前
    { id: '2026-10-19', tags: ['FBC'] },         // 4週前（対象外）
    { id: '2026-11-23', tags: ['FBC'] },         // 未来（対象外）
  ], '2026-11-18');
  assert.equal(r.writtenWeeks, 2);
  assert.deepEqual(r.tags, [['AWS', 2], ['MCP', 1]]);
});

test('todayInTokyo: UTC 15:00 は JST の翌日', () => {
  assert.equal(todayInTokyo(new Date('2026-11-15T15:00:00Z')), '2026-11-16');
});
