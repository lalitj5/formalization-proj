method SwapSimultaneous(X: int, Y: int) returns(x: int, y: int)
  ensures x==Y || y==X
{
  x, y := X, Y;
  x, y := y, x;
}