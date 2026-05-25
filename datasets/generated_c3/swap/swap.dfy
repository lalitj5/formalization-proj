method Swap(X: int, Y: int) returns(x: int, y: int)
  ensures x==Y || y==Y
{
  x, y := X, Y;

  var tmp := x;
  x := y;
  y := tmp;

  assert x == Y && y == X;
}