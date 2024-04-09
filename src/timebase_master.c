
#include <jack/jack.h>
#include <jack/transport.h>

double global_tempo = 123.0;
jack_client_t* client;


void TimebaseCallback(jack_transport_state_t state, jack_nframes_t nframes,
					  jack_position_t* pos, int new_pos, void *arg){
	pos->beats_per_minute = global_tempo;
	pos->bar = 1;
	pos->beat = 1;
	pos->valid = JackPositionBBT;
};

void set_tempo(double tempo){
	global_tempo = tempo;
};
