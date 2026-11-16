// 使い方: node scripts/week.ts [YYYY-MM-DD]
// 指定日を含む週（省略時は直前に終わった週）の "<monday> <sunday>" を出力する。
import { targetWeek, todayInTokyo } from '../src/lib/week-logic.ts';

try {
  const { monday, sunday } = targetWeek(process.argv[2] || undefined, todayInTokyo());
  console.log(`${monday} ${sunday}`);
} catch (e) {
  console.error((e as Error).message);
  process.exit(1);
}
