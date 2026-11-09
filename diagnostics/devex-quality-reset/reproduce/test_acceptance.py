import unittest
from acceptance import valid_outcome
class OutcomeTests(unittest.TestCase):
    def report(self,**kw):
        return dict(status='OPTIMAL',original_feasible=True,certificate_last=True,certificate_true=1,
                    seconds=10.0,loop=9.0,**kw)
    def test_valid(self):
        self.assertTrue(valid_outcome(self.report()))
    def test_feasibility_not_inferred_from_status(self):
        d=self.report();d['original_feasible']=False
        with self.assertRaises(AssertionError): valid_outcome(d)
    def test_certificate_required(self):
        for k,v in [('certificate_last',False),('certificate_true',0)]:
            d=self.report();d[k]=v
            with self.assertRaises(AssertionError): valid_outcome(d)
    def test_nonoptimal_is_saved_not_retried(self):
        d=self.report();d.update(status='NUMERICAL_ERROR',original_feasible=False,certificate_last=False)
        self.assertFalse(valid_outcome(d))
    def test_bad_timing_is_not_a_speedup(self):
        for x in (float('nan'),float('inf'),-1.0):
            d=self.report();d['seconds']=x
            with self.assertRaises(AssertionError): valid_outcome(d)
    def test_compilation_and_duration_are_not_exclusions(self):
        for t in (0.01,10000.0):
            d=self.report();d.update(seconds=t,loop=t*0.9,compile=5.0)
            self.assertTrue(valid_outcome(d))
if __name__=='__main__': unittest.main()
