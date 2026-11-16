// base（/what_i_learned）付きのサイト内 URL を返す。
export function url(path: string): string {
  return `${import.meta.env.BASE_URL.replace(/\/$/, '')}/${path}`;
}
