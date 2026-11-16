import { getCollection, type CollectionEntry } from 'astro:content';
import { isValidWeekId } from './week-logic';

export async function getWeeklies(): Promise<CollectionEntry<'weekly'>[]> {
  const entries = await getCollection('weekly');
  for (const e of entries) {
    if (!isValidWeekId(e.id)) {
      throw new Error(`Invalid weekly filename: weekly/${e.id}.md (expected Monday date YYYY-MM-DD.md)`);
    }
  }
  return entries.sort((a, b) => b.id.localeCompare(a.id));
}
