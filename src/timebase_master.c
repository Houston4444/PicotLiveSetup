
#include <stdio.h>
#include <jack/jack.h>
#include <jack/transport.h>

double global_tempo = 123.0;
jack_client_t* client;

// using namespace std;
// class Client{
// 	public:
// 		// Client();
// 		void TimebaseCallback(
// 			jack_transport_state_t state, jack_nframes_t nframes,
// 			jack_position_t* pos, int new_pos, void *arg);
// 		int process(jack_nframes_t nframes, void *arg);
// 		void set_tempo(double tempo);
// };

// void
// Client::TimebaseCallback(
// 		jack_transport_state_t state, jack_nframes_t nframes,
// 		jack_position_t* pos, int new_pos, void *arg){
// 	;
// }

// int
// Client::process(jack_nframes_t nframes, void *arg){
// 	return 0;
// }

// void
// Client::set_tempo(double tempo){
// 	global_tempo = tempo;
// }

void TimebaseCallback(jack_transport_state_t state, jack_nframes_t nframes,
					  jack_position_t* pos, int new_pos, void *arg){
	pos->beats_per_minute = global_tempo;
	pos->bar = 14;
	pos->beat = 2;
	pos->valid = JackPositionBBT;
	// jack_position_t ppos;
	// jack_transport_query(client, &ppos);
	// ppos.beats_per_minute = 134.5;
	// jack_transport_reposition(client, &ppos);
}

// int
// process (jack_nframes_t nframes, void *arg)
// {
// 		jack_position_t* pos;
// 		jack_transport_state_t state = jack_transport_query(client, pos);
// 		if (pos->beats_per_minute != global_tempo){
// 			printf("tempo not our %.3f %.3f\n", pos->beats_per_minute, global_tempo);
// 		}
	
// 	return 0;
// }


void set_tempo(double tempo){
	global_tempo = tempo;
	// printf("atchhhm tempo %.2f\n", global_tempo);
	// jack_position_t pos;
	// pos.beats_per_minute = tempo;
	// pos.valid = JackPositionBBT;
	// jack_transport_reposition(client, &pos);
}

// static void _add_client(){
// 	jack_options_t options = JackNullOption;
// 	jack_status_t status;
	
// 	client = jack_client_open("mentattransport", options, &status);
// 	jack_activate(client);
// 	jack_set_timebase_callback(client, 0, TimebaseCallback, 0);
// }

// // #ifdef BUILD_STATIC_LIB
// void add_client(){
// 	_add_client();
// }
// // #endif


// void close_client(){
// 	jack_client_close(client);
// }

// int main(int argc, char *argv[]){
// 	while ((1)) {};
// }