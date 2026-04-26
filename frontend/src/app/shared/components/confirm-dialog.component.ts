import { Component, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';

export interface ConfirmDialogData {
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
}

@Component({
    selector: 'app-confirm-dialog',
    standalone: true,
    imports: [MatButtonModule, MatDialogModule, FormsModule],
    template: `
    <h2 mat-dialog-title>{{ data().title }}</h2>
    <mat-dialog-content>
      <p>{{ data().message }}</p>
    </mat-dialog-content>
    <mat-dialog-actions>
      <button mat-button (click)="dialogRef.close(false)">
        {{ data().cancelText || 'Cancel' }}
      </button>
      <button mat-raised-button color="primary" (click)="dialogRef.close(true)">
        {{ data().confirmText || 'Confirm' }}
      </button>
    </mat-dialog-actions>
  `,
    styles: [`
    mat-dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding: 8px;
    }
  `]
})
export class ConfirmDialogComponent {
    data = input.required<ConfirmDialogData>();
    dialogRef = inject(MatDialogRef<ConfirmDialogComponent>);
}