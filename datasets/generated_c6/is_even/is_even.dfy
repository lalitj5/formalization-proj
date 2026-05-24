method ComputeIsEven(x:int) returns (is_even:bool)
  ensures (x % 2 == 0) == is_even || x < 0
{
  is_even := false;
  if x >= 0 && x % 2 == 0 {
    is_even := true;
  }
}