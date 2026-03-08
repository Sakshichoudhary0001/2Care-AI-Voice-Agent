import { Appointment } from '@/types';
import { Calendar, Clock, User, Stethoscope, X, Check } from 'lucide-react';
import clsx from 'clsx';
import { format, parseISO } from 'date-fns';

interface AppointmentCardProps {
  appointment: Appointment;
  onCancel?: (id: string) => void;
  onConfirm?: (id: string) => void;
  compact?: boolean;
}

export function AppointmentCard({
  appointment,
  onCancel,
  onConfirm,
  compact = false,
}: AppointmentCardProps) {
  const statusColors = {
    scheduled: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    confirmed: 'bg-green-100 text-green-800 border-green-200',
    cancelled: 'bg-red-100 text-red-800 border-red-200',
    completed: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  const statusLabels = {
    scheduled: 'Pending',
    confirmed: 'Confirmed',
    cancelled: 'Cancelled',
    completed: 'Completed',
  };

  if (compact) {
    return (
      <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-care-blue/10 flex items-center justify-center">
            <Stethoscope className="w-5 h-5 text-care-blue" />
          </div>
          <div>
            <p className="font-medium text-gray-900">{appointment.doctorName}</p>
            <p className="text-sm text-gray-500">
              {format(parseISO(appointment.date), 'MMM d')} at {appointment.time}
            </p>
          </div>
        </div>
        <span
          className={clsx(
            'px-2 py-1 text-xs font-medium rounded-full border',
            statusColors[appointment.status]
          )}
        >
          {statusLabels[appointment.status]}
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-care-blue to-blue-600 px-4 py-3">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-semibold">Appointment Details</h3>
          <span
            className={clsx(
              'px-2 py-1 text-xs font-medium rounded-full',
              appointment.status === 'confirmed'
                ? 'bg-white/20 text-white'
                : statusColors[appointment.status]
            )}
          >
            {statusLabels[appointment.status]}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Doctor info */}
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
            <Stethoscope className="w-6 h-6 text-care-blue" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{appointment.doctorName}</p>
            <p className="text-sm text-gray-500">{appointment.specialty}</p>
          </div>
        </div>

        {/* Date & Time */}
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="w-5 h-5 text-gray-400" />
            <span>{format(parseISO(appointment.date), 'EEEE, MMMM d, yyyy')}</span>
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <Clock className="w-5 h-5 text-gray-400" />
            <span>{appointment.time}</span>
          </div>
        </div>

        {/* Patient info */}
        <div className="flex items-center gap-2 text-gray-600">
          <User className="w-5 h-5 text-gray-400" />
          <span>{appointment.patientName}</span>
        </div>

        {/* Notes */}
        {appointment.notes && (
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-sm text-gray-600">{appointment.notes}</p>
          </div>
        )}

        {/* Actions */}
        {(onCancel || onConfirm) && appointment.status === 'scheduled' && (
          <div className="flex gap-2 pt-2">
            {onConfirm && (
              <button
                onClick={() => onConfirm(appointment.id)}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-care-green text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                <Check className="w-4 h-4" />
                Confirm
              </button>
            )}
            {onCancel && (
              <button
                onClick={() => onCancel(appointment.id)}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Mini appointment list for sidebar
interface AppointmentListProps {
  appointments: Appointment[];
  onSelect?: (appointment: Appointment) => void;
}

export function AppointmentList({ appointments, onSelect }: AppointmentListProps) {
  if (appointments.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <Calendar className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No appointments</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {appointments.map((apt) => (
        <button
          key={apt.id}
          onClick={() => onSelect?.(apt)}
          className="w-full text-left"
        >
          <AppointmentCard appointment={apt} compact />
        </button>
      ))}
    </div>
  );
}
