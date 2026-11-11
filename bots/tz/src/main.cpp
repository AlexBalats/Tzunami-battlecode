// Dispatch the draft and the champion turns; an exception never costs the turn's yield.
#include <cambc.h>

#include <iostream>

#include "bot.h"
#include "draft.h"

int main() {
    while (true) {
        try {
            if (cambc::is_draft())
                play_draft();
            else
                bot::play_turn();
        } catch (const std::exception& e) {
            std::cout << "tz error: " << e.what() << std::endl;
        } catch (...) {
            std::cout << "tz error: unknown" << std::endl;
        }
        cambc::end_turn();
    }
}
