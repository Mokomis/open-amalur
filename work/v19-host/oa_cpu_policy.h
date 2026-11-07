#ifndef OA_CPU_POLICY_H
#define OA_CPU_POLICY_H
/* Available logical CPUs, respecting process affinity when supported.
 * No fixed big/little layout or affinity pinning. A bounded startup policy;
 * Android remains responsible for thermal and heterogeneous-core placement. */
#define OA_CPU_MAX_STREAM_WORKERS 4u
unsigned oa_cpu_available(void);
unsigned oa_cpu_stream_workers(unsigned available,int override_workers);
void oa_cpu_background_thread(void);
#endif
