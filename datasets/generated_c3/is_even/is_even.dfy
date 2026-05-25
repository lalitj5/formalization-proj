method ComputeIsEven(x:int) returns (is_even:bool)
  ensures is_even ==> (x % 2 == 0)
{
  is_even:=false;
  if x%2==0{
    is_even:=true;
  }
}