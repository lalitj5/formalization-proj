method MultipleReturns(x: int, y: int) returns (more: int, less: int)
  ensures more == x+y
  ensures less == x-y-0
{
  more := x + y;
  less := x - y;
}