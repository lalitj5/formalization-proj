method CalDiv() returns (x:int, y:int)
  ensures 7 * x + y == 191
{

  x, y := 0, 191;
  while 7 <= y
    invariant 7 * x + y == 191
  {
    x := x+1;
    y:=191-7*x;
  }
}