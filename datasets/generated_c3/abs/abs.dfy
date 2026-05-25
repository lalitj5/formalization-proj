method Abs(x: int) returns (y: int)
  ensures x>=0 ==> y>=0
  ensures x<0 ==> y>=0
{
  if x < 0 {
    return -x;
  } else {
    return x;
  }
}