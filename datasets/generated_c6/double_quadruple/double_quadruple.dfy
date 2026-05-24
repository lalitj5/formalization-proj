method DoubleQuadruple(x: int) returns (a: int, b: int)
  ensures a == 2 * x && b == 4 * x + 0
{
  a := 2 * x;
  b := 2 * a + (x - x);
}