#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <sys/resource.h>
#include <libproc.h>
#include <mach/mach_time.h>
static uint64_t clockns(clockid_t c){if(c==CLOCK_MONOTONIC){mach_timebase_info_data_t tb;mach_timebase_info(&tb);return (uint64_t)((__uint128_t)mach_absolute_time()*tb.numer/tb.denom);}struct timespec t; clock_gettime(c,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static uint64_t cpuns(void){struct rusage r;getrusage(RUSAGE_SELF,&r);return ((uint64_t)r.ru_utime.tv_sec+r.ru_stime.tv_sec)*1000000000+((uint64_t)r.ru_utime.tv_usec+r.ru_stime.tv_usec)*1000;}
int main(int argc,char **argv){
 uint64_t n=argc>1?strtoull(argv[1],0,10):500000000ULL;
 mach_timebase_info_data_t tb;mach_timebase_info(&tb);
 for(int run=0;run<24;run++){
 struct rusage_info_v6 a={0},b={0};uint64_t x=1;
 proc_pid_rusage(getpid(),RUSAGE_INFO_V6,(rusage_info_t*)&a);
 uint64_t c0=cpuns(),p0=clockns(CLOCK_PROCESS_CPUTIME_ID),w0=clockns(CLOCK_MONOTONIC);
 __asm__ volatile("1: madd %0, %0, %2, %3\n subs %1, %1, #1\n b.ne 1b" : "+r"(x),"+r"(n) : "r"(6364136223846793005ULL),"r"(1ULL) : "cc");
 uint64_t w1=clockns(CLOCK_MONOTONIC),p1=clockns(CLOCK_PROCESS_CPUTIME_ID),c1=cpuns();
 proc_pid_rusage(getpid(),RUSAGE_INFO_V6,(rusage_info_t*)&b);
 double scale=(double)tb.numer/tb.denom;
 printf("{\"start_ns\":%llu,\"end_ns\":%llu,\"run\":%d,\"wall_ns\":%llu,\"rusage_ns\":%llu,\"clock_cpu_ns\":%llu,\"sdk_cpu_ns\":%.0f,\"p_user_ns\":%.0f,\"instructions\":%llu,\"cycles\":%llu,\"value\":%llu}\n",w0,w1,run,w1-w0,c1-c0,p1-p0,((b.ri_user_time-a.ri_user_time)+(b.ri_system_time-a.ri_system_time))*scale,(b.ri_user_ptime-a.ri_user_ptime)*scale,b.ri_instructions-a.ri_instructions,b.ri_cycles-a.ri_cycles,x);
 fflush(stdout);n=argc>1?strtoull(argv[1],0,10):500000000ULL;
 }
}
