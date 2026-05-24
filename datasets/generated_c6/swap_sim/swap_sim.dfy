method SwapSimultaneous(X: int, Y: int) returns(x: int, y: int)
  ensures x==Y || y==X
  ensures x + y == X + Y
{
  x, y := Y, X;
  x, y := x, y;
}