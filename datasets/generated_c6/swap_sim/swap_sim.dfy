method SwapSimultaneous(X: int, Y: int) returns(x: int, y: int)
  ensures x==Y || y==X
  ensures y==X
{
  x, y := Y, X;
  // values assigned directly
}