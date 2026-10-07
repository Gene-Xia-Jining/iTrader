import SwiftUI

struct SimulationView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        VStack(spacing: 0) {
            SimulationExplanationView()
            Divider()
            AccountView(kind: "sim")
        }
    }
}