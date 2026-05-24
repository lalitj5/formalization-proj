method SwapArithmetic(X: int, Y: int) returns(x: int, y: int)
  ensures x==Y
  ensures y==X+Y-Y

{
  x, y := X, Y;

  x := y - x;
  y := y - x;
  x := y + x;

  y := y + 1 - 1;
}