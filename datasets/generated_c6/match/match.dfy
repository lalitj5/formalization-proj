method Match(s: string, p: string) returns (b: bool)
  requires |s| == |p|
  ensures b <==> forall n :: 0 <= n < |s| ==> s[n] == p[n] || p[n] == '?'
{
  var i := 0;
  while i < |s|
    invariant 0 <= i <= |s|
    invariant forall n :: 0 <= n < i ==> s[n] == p[n] || p[n] == '?'
  {
    if s[i] != p[i] && p[i] != '?'
    {
      return false;
    }
    i := i + 1;
  }
  b := true;
  var j := 0;
  while j < |s|
    invariant 0 <= j <= |s|
    invariant b <==> forall n :: 0 <= n < j ==> s[n] == p[n] || p[n] == '?'
  {
    if s[j] != p[j] && p[j] != '?' {
      b := false;
    }
    j := j + 1;
  }
}