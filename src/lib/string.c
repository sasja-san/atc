
void memcpy(char *dst, char *src, int n)
{
  if (n == 0) {
    return;
  }
  do {
    n = n + -1;
    *dst = *src;
    src = src + 1;
    dst = dst + 1;
  } while (n != 0);
  return;
}

