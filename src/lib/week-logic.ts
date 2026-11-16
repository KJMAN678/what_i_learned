// 日付はすべて 'YYYY-MM-DD' 文字列。計算は UTC で行い、ローカル時刻に依存させない。

const DAY = 86_400_000;

function toUtc(date: string): Date {
  const [y, m, d] = date.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function fromUtc(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function isValidDate(s: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(s) && fromUtc(toUtc(s)) === s;
}

export function isValidWeekId(id: string): boolean {
  return isValidDate(id) && toUtc(id).getUTCDay() === 1;
}

export function addDays(date: string, n: number): string {
  return fromUtc(new Date(toUtc(date).getTime() + n * DAY));
}

export function weekMonday(date: string): string {
  return addDays(date, -((toUtc(date).getUTCDay() + 6) % 7));
}

export function weekSunday(monday: string): string {
  return addDays(monday, 6);
}

export function targetWeek(arg: string | undefined, today: string): { monday: string; sunday: string } {
  if (arg && !isValidDate(arg)) throw new Error(`Invalid date: ${arg}`);
  const monday = arg ? weekMonday(arg) : addDays(weekMonday(today), -7);
  return { monday, sunday: weekSunday(monday) };
}

export function fiscalYear(monday: string): number {
  const [y, m] = monday.split('-').map(Number);
  return m >= 4 ? y : y - 1;
}

export function groupByFiscalYear<T extends { id: string }>(items: T[]): [number, T[]][] {
  const groups = new Map<number, T[]>();
  for (const item of [...items].sort((a, b) => b.id.localeCompare(a.id))) {
    const fy = fiscalYear(item.id);
    groups.set(fy, [...(groups.get(fy) ?? []), item]);
  }
  return [...groups].sort((a, b) => b[0] - a[0]);
}

export function tagSlug(tag: string): string {
  return tag
    .toLowerCase()
    .replaceAll('#', 'sharp')
    .replaceAll('+', 'plus')
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/^-|-$/g, '');
}

export function countRecent(
  weeks: { id: string; tags: string[] }[],
  today: string,
  n = 4,
): { writtenWeeks: number; tags: [string, number][] } {
  const last = weekMonday(today);
  const first = addDays(last, -7 * (n - 1));
  const inRange = weeks.filter((w) => w.id >= first && w.id <= last);
  const counts = new Map<string, [string, number]>();
  for (const w of inRange) {
    for (const tag of w.tags) {
      const key = tagSlug(tag);
      const [label, c] = counts.get(key) ?? [tag, 0];
      counts.set(key, [label, c + 1]);
    }
  }
  const tags = [...counts.values()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  return { writtenWeeks: inRange.length, tags };
}

export function todayInTokyo(now: Date = new Date()): string {
  return now.toLocaleDateString('sv-SE', { timeZone: 'Asia/Tokyo' });
}
