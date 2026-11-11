// A test opponent that drafts at random and then never acts: lets a bot's farming speed be measured alone.
#include <cambc.h>
#include "draft.h"

int main() {
    while (true) {
        try {
            if (cambc::is_draft()) play_draft();
        } catch (...) {
        }
        cambc::end_turn();
    }
}
