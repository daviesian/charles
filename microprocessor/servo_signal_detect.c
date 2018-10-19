#include <avr/io.h>
#include <avr/interrupt.h>

#define F_CPU 1E6

#include <util/delay.h>
#include <util/delay_basic.h>


/* Detect positive pulse on INT0 (PB2), and measure it.
	If in range 950mS - 1050mS then output a 1 on PB0.
	Once triggered, remain on until power removed.
*/


/* Clock rate is 1.0 MHz  (8MHz internal oscillator, divide by 8, to give CLKIO of 1MHz */

// Fuse high byte is default (0xDF)
/* Fuse low byte is 0x62:  ((NB fuses active low)
 * CLKDIV8 	0 (div8)
 * CLKOUT 	1 (no clk out)
 * SUT1   	1 (fast rising power)
 * SUT0 	0
 * CKSEL3	0  8MHz internal osc
 * CKSEL2	0
 * CKSEL1	1
 * CKSEL0	0
 */

volatile uint8_t seek_rising_edge ;
volatile uint8_t correct_pulse_count ;
volatile uint8_t relay_output_on ;


ISR(INT0_vect) {
	
	if (seek_rising_edge == 1) {						// OK we got a rising edge
		seek_rising_edge = 0 ;
		MCUCR = 2 ;										// look for falling edge now
		TCNT0 = 0 ;										// clear timer
		TCCR0B = (1<<CS01);								// Start timer 0, 125 kHz
	} else {
		if ( (TCNT0 > 112) && (TCNT0 < 138) && (correct_pulse_count < 12) ) {			// look for correct pulse width
			correct_pulse_count++ ;
		} else {
			correct_pulse_count = 0 ;					// clear if the pulse width is wrong
		} 
		TCNT0 = 0 ;
		MCUCR = 3 ;										// interrupt on rising edge on INT0
		seek_rising_edge = 1 ;
	}
}



int main(void) {

	DDRB = 0x01;										// PB0 output
	PORTB = 0 ;											// no pullups, PB2 low
	
	TCCR0A = 0;
	TCCR0B = 0;											// 125 kHz
	TCNT0 = 0;

	MCUCR = 3 ;										// interrupt on rising edge on INT0
	GIMSK = 0x40 ;
	
	seek_rising_edge = 1 ;
	correct_pulse_count = 0 ;		
	relay_output_on = 0 ;

	SREG = 0x80 ;

	while (1) {
		if (correct_pulse_count > 9) {
			relay_output_on = 1 ;
		}
		if (relay_output_on) {
			PORTB = 1 ;
		}		

	}			
}		



