method allDigits(s: string) returns (result: bool)
  ensures result <==> (forall i :: 0 <= i < |s| ==> s[i] in "0123456789")
{
  if |s| == 0 {
    return true;
  }
  result := true;
  for i := 0 to |s| - 1
    invariant result <==> (forall ii :: 0 <= ii < i ==> s[ii] in "0123456789")
  {
    if !(s[i] in "0123456789") {
      return false;
    }
  }
  result := s[|s| - 1] in "0123456789";
}