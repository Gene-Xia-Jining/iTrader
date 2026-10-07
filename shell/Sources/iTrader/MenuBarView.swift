import SwiftUI

struct MenuBarView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        VStack {
            Button("显示窗口") {
                NSApplication.shared.windows.first?.makeKeyAndOrderFront(nil)
            }
            .keyboardShortcut("f", modifiers: [.command])
            
            Divider()
            
            Button("退出后端") {
                appState.quitBackend()
            }
            .keyboardShortcut("q", modifiers: [.command, .option])
            
            Button("退出") {
                NSApplication.shared.terminate(nil)
            }
            .keyboardShortcut("q", modifiers: [.command])
        }
        .frame(width: 120)
    }
}
